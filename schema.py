from datetime import date
import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# =========================================================
# VALID CURRENCY CODES
# =========================================================

VALID_CURRENCIES = {
    "USD",
    "INR",
    "EUR",
    "GBP",
    "CAD",
    "AUD",
    "JPY",
    "AED",
    "SGD",
    "CHF",
}


# =========================================================
# CURRENCY SYMBOL → ALLOWED ISO CODES
# =========================================================

SYMBOL_ISO_MAP = {
    "$": {"USD", "CAD", "AUD", "SGD", "NZD", "HKD"},
    "₹": {"INR"},
    "RS": {"INR"},
    "RS.": {"INR"},
    "€": {"EUR"},
    "£": {"GBP"},
    "CA$": {"CAD"},
    "A$": {"AUD"},
    "¥": {"JPY"},
    "AED": {"AED"},
    "S$": {"SGD"},
    "CHF": {"CHF"},
}


# =========================================================
# LINE ITEM MODEL
# =========================================================

class LineItem(BaseModel):

    item_name: str = Field(
        description="Name or description of the line item."
    )

    quantity: Optional[float] = Field(
        default=1.0,
        description="Quantity purchased."
    )

    unit_price: Optional[float] = Field(
        default=None,
        description="Price per unit."
    )

    total_price: Optional[float] = Field(
        default=None,
        description="Total line cost."
    )


# =========================================================
# DOCUMENT MODEL
# =========================================================

class ExtractedDocument(BaseModel):

    biller_name: Optional[str] = Field(
        default=None,
        description="Vendor or biller name."
    )

    document_type: Optional[str] = Field(
        default=None,
        description="Document type (invoice, receipt, utility bill, etc.)."
    )

    document_date: Optional[date] = Field(
        default=None,
        description="Document date (YYYY-MM-DD)."
    )

    subtotal_amount: Optional[float] = Field(
        default=None,
        description="Subtotal before tax."
    )

    tax_amount: Optional[float] = Field(
        default=0.0,
        description="Total tax amount."
    )

    discount_amount: Optional[float] = Field(
        default=0.0,
        description="Total discount amount."
    )

    total_amount: Optional[float] = Field(
        default=None,
        description="Stated total amount."
    )

    currency: Optional[str] = Field(
        default=None,
        description="3-letter ISO 4217 currency code."
    )

    raw_text_context: Optional[str] = Field(
        default=None,
        description="Original raw document text used for validation."
    )

    line_items: Optional[List[LineItem]] = Field(
        default_factory=list,
        description="Itemized list of purchased items."
    )

    summary: Optional[str] = Field(
        default=None,
        description="Short summary of the document."
    )

    validation_discrepancies: List[str] = Field(
        default_factory=list,
        description="Human-readable discrepancies detected in the document."
    )


    # =====================================================
    # CURRENCY CODE VALIDATION
    # =====================================================

    @field_validator("currency")
    @classmethod
    def validate_currency_code(
        cls,
        v: Optional[str]
    ) -> Optional[str]:

        if v is None:
            return None

        v_upper = v.strip().upper()

        return v_upper


    # =====================================================
    # DATE VALIDATION
    # =====================================================

    @field_validator("document_date")
    @classmethod
    def validate_date_bounds(
        cls,
        v: Optional[date]
    ) -> Optional[date]:

        if v is None:
            return None

        min_date = date(1900, 1, 1)
        max_date = date(2027, 12, 31)

        if not (min_date <= v <= max_date):
            return None

        return v


    # =====================================================
    # DOCUMENT DISCREPANCY VALIDATION
    # =====================================================

    @model_validator(mode="after")
    def record_document_discrepancies(
        self
    ) -> "ExtractedDocument":

        # Always clear previous warnings.
        self.validation_discrepancies = []


        # =================================================
        # 1. CURRENCY SYMBOL VS ISO CURRENCY CHECK
        # =================================================

        if self.currency and self.raw_text_context:

            raw_upper = self.raw_text_context.upper()

            for symbol, allowed_isos in SYMBOL_ISO_MAP.items():

                # -------------------------------------------------
                # IMPORTANT:
                #
                # We DO NOT use:
                #
                #     if symbol in raw_upper
                #
                # because "RS" would incorrectly match:
                #
                #     Retailers
                #
                # -------------------------------------------------

                # Currency markers must not be embedded inside
                # normal alphabetic words.
                pattern = (
                    rf"(?<![A-Z])"
                    rf"{re.escape(symbol)}"
                    rf"(?![A-Z])"
                )

                if re.search(pattern, raw_upper):

                    # If the extracted ISO code is compatible
                    # with the detected symbol, everything is fine.
                    if self.currency in allowed_isos:
                        continue

                    # Otherwise report the conflict.
                    msg = (
                        f"Currency Discrepancy: Document text contains "
                        f"'{symbol}', which conflicts with extracted ISO "
                        f"currency code '{self.currency}'."
                    )

                    if msg not in self.validation_discrepancies:
                        self.validation_discrepancies.append(msg)


        # =================================================
        # 2. LINE ITEM TOTAL VALIDATION
        # =================================================

        if self.line_items and self.total_amount is not None:

            items_sum = 0.0
            has_valid_items = False

            for item in self.line_items:

                # -------------------------------------------------
                # Case 1:
                # Gemini extracted an explicit total_price
                # -------------------------------------------------

                if item.total_price is not None:

                    items_sum += item.total_price
                    has_valid_items = True

                # -------------------------------------------------
                # Case 2:
                # Calculate quantity × unit price
                # -------------------------------------------------

                elif (
                    item.unit_price is not None
                    and item.quantity is not None
                ):

                    items_sum += (
                        item.unit_price * item.quantity
                    )

                    has_valid_items = True


            if has_valid_items:

                computed = round(
                    items_sum
                    + (self.tax_amount or 0.0)
                    - (self.discount_amount or 0.0),
                    2
                )

                # Allow a small floating-point tolerance.
                if abs(computed - self.total_amount) > 0.05:

                    currency_display = self.currency or ""

                    msg = (
                        f"Math Discrepancy: Sum of line items "
                        f"({currency_display} {computed:.2f}) "
                        f"does not match stated document total "
                        f"({currency_display} {self.total_amount:.2f})."
                    )

                    self.validation_discrepancies.append(msg)


        return self


    # =====================================================
    # COMPUTED TOTAL PROPERTY
    # =====================================================

    @property
    def computed_total(self) -> Optional[float]:

        if not self.line_items:
            return self.total_amount

        items_sum = 0.0

        for item in self.line_items:

            if item.total_price is not None:

                items_sum += item.total_price

            elif (
                item.unit_price is not None
                and item.quantity is not None
            ):

                items_sum += (
                    item.unit_price * item.quantity
                )


        return round(
            items_sum
            + (self.tax_amount or 0.0)
            - (self.discount_amount or 0.0),
            2
        )