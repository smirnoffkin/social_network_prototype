"""add follows table

Revision ID: 732d783fce7d
Revises: fbaebd6e05c8
Create Date: 2023-06-11 23:33:27.902158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '732d783fce7d'
down_revision = 'fbaebd6e05c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('follows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('follower_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('follows')
    # ### end Alembic commands ###
