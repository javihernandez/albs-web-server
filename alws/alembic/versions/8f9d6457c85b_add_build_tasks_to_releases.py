"""Add build tasks to releases

Revision ID: 8f9d6457c85b
Revises: 585ab06efb32
Create Date: 2021-11-22 11:32:44.367676

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f9d6457c85b'
down_revision = '585ab06efb32'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('build_releases', sa.Column('build_tasks_ids', sa.ARRAY(sa.Integer(), dimensions=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('build_releases', 'build_tasks_ids')
    # ### end Alembic commands ###
