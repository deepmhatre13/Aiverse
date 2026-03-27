from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import logging

logger = logging.getLogger(__name__)


def generate_payment_receipt_pdf(payment):
    """
    Payment receipt PDF generation is disabled.
    
    The platform removed the receipts feature; this helper intentionally
    returns None to avoid runtime/maintenance issues.
    """
    return None