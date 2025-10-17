"""Add is_archived to WarehouseStock

Revision ID: a7d70aab5170
Revises: 00e935864a9c
Create Date: 2025-07-11 20:50:22.541868

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7d70aab5170'
down_revision = '00e935864a9c'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('warehouse_stock', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=True))

def downgrade():
    with op.batch_alter_table('warehouse_stock', schema=None) as batch_op:
        batch_op.drop_column('is_archived')

    # ### end Alembic commands ###
