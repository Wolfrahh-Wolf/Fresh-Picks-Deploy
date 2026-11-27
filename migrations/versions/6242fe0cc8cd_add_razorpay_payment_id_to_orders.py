"""add razorpay_payment_id to orders

Revision ID: 6242fe0cc8cd
Revises: 7d2cabba4728
Create Date: 2026-11-27 19:34:22.567269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6242fe0cc8cd'
down_revision: Union[str, Sequence[str], None] = '7d2cabba4728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('razorpay_payment_id', sa.String(length=128), nullable=True))
    op.create_unique_constraint('uq_orders_razorpay_payment_id', 'orders', ['razorpay_payment_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_orders_razorpay_payment_id', 'orders', type_='unique')
    op.drop_column('orders', 'razorpay_payment_id')
