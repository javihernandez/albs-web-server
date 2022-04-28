"""Added platform priority

Revision ID: 0854c43a70db
Revises: 433fd427f579
Create Date: 2022-04-28 19:05:06.111213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0854c43a70db'
down_revision = '433fd427f579'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('platforms', sa.Column('priority', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('platforms', 'priority')
    # ### end Alembic commands ###
