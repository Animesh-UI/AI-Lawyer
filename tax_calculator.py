import matplotlib.pyplot as plt
from fpdf import FPDF

STANDARD_DEDUCTION = 50000


# =========================
# OLD REGIME TAX
# =========================
def old_regime_tax(income, hra=0, sec80c=0, sec80d=0):
    taxable_income = income - hra - sec80c - sec80d - STANDARD_DEDUCTION

    if taxable_income < 0:
        taxable_income = 0

    tax = 0

    if taxable_income <= 250000:
        tax = 0

    elif taxable_income <= 500000:
        tax = (taxable_income - 250000) * 0.05

    elif taxable_income <= 1000000:
        tax = 12500 + (taxable_income - 500000) * 0.20

    else:
        tax = 112500 + (taxable_income - 1000000) * 0.30

    return tax, taxable_income


# =========================
# NEW REGIME TAX
# =========================
def new_regime_tax(income):
    taxable_income = income - STANDARD_DEDUCTION

    if taxable_income < 0:
        taxable_income = 0

    tax = 0

    slabs = [
        (300000, 0),
        (600000, 0.05),
        (900000, 0.10),
        (1200000, 0.15),
        (1500000, 0.20),
    ]

    prev = 0

    for limit, rate in slabs:
        if taxable_income > limit:
            tax += (limit - prev) * rate
            prev = limit
        else:
            tax += (taxable_income - prev) * rate
            return tax, taxable_income

    tax += (taxable_income - 1500000) * 0.30

    return tax, taxable_income


# =========================
# HRA CALCULATION
# =========================
def hra_deduction(basic, hra_received, rent, metro=True):
    if metro:
        percent_salary = 0.50 * basic
    else:
        percent_salary = 0.40 * basic

    rent_minus_salary = rent - (0.10 * basic)

    hra_exempt = min(
        hra_received,
        percent_salary,
        rent_minus_salary
    )

    return max(hra_exempt, 0)


# =========================
# GST CALCULATOR
# =========================
def gst_calculator(amount, gst_rate):
    gst_amount = amount * gst_rate / 100
    total = amount + gst_amount
    return gst_amount, total


# =========================
# TDS CALCULATOR
# =========================
def tds_calculator(amount, rate):
    tds = amount * rate / 100
    return tds


# =========================
# BUSINESS TAX
# =========================
def business_tax(profit):
    if profit <= 250000:
        return 0
    else:
        return profit * 0.25


# =========================
# TAX CHART
# =========================
def tax_chart(old_tax, new_tax):
    labels = ["Old Regime", "New Regime"]
    values = [old_tax, new_tax]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Tax Comparison")
    plt.ylabel("Tax Amount")

    plt.savefig("tax_chart.png")
    plt.close()


# =========================
# PDF EXPORT
# =========================
def export_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Tax Report", ln=True)

    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

    pdf.image("tax_chart.png", x=10, y=100, w=100)

    filename = "tax_report.pdf"
    pdf.output(filename)

    return filename
