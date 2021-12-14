"""Create couple new tables for export repositories from pulp.

Revision ID: aa0a3bdf68d4
Revises: e88b665182b9
Create Date: 2021-12-14 11:59:44.319151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa0a3bdf68d4'
down_revision = 'e88b665182b9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('export_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('exported_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('repo_exporters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('path', sa.Text(), nullable=False),
    sa.Column('exported_id', sa.Integer(), nullable=False),
    sa.Column('repository_id', sa.Integer(), nullable=False),
    sa.Column('fs_exporter_href', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['exported_id'], ['export_tasks.id'], ),
    sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('repo_exporters')
    op.drop_table('export_tasks')
    # ### end Alembic commands ###
