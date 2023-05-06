import re
import uuid
from enum import Enum
from typing import List

from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone


class MemoType(Enum):
    EXPENSE_CATEGORY = "Expense Category"
    JOB_ADDRESS = "Job Address"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    uuid = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4)
    date = models.DateField()
    entry_type = models.CharField(choices=TransactionType.choices, max_length=7)
    amount = models.IntegerField()
    memo = models.CharField(max_length=16)

    @property
    def amount_in_dollar(self):
        return self.readable_amount(self.amount)

    @staticmethod
    def readable_amount(value):
        return round(value / 100, 2)

    def memo_type(self) -> MemoType:
        address_regex = r"^\d+\s+[A-z0-9]+\s*[A-z0-9]*$"
        MEMO_TYPE_FROM_ADDRESS = {
            True: MemoType.JOB_ADDRESS,
            False: MemoType.EXPENSE_CATEGORY,
        }
        return MEMO_TYPE_FROM_ADDRESS[bool(re.match(address_regex, self.memo))].value

    @classmethod
    def get_report(cls):
        transactions: List[Transaction] = cls.objects.all()
        expenses = 0
        gross_revenue = 0
        for transaction in transactions:
            if transaction.entry_type == cls.TransactionType.EXPENSE:
                expenses += transaction.amount
            else:
                gross_revenue += transaction.amount

        net_revenue = gross_revenue - expenses

        return {
            "expenses": cls.readable_amount(expenses),
            "gross-revenue": cls.readable_amount(gross_revenue),
            "net-revenue": cls.readable_amount(net_revenue),
        }
