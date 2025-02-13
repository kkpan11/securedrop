"""dropped session_nonce from journalist table and revoked tokens table
   due to new session implementation

Revision ID: c5a02eb52f2d
Revises: b7f98cfd6a70
Create Date: 2022-04-16 21:25:22.398189

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5a02eb52f2d"
down_revision = "b7f98cfd6a70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("revoked_tokens")
    with op.batch_alter_table("journalists", schema=None) as batch_op:
        batch_op.drop_column("session_nonce")

    # ### end Alembic commands ###


def downgrade() -> None:
    """This would have been the easy way, however previous does not have
    default value and thus up/down assertion fails"""
    # op.add_column('journalists', sa.Column('session_nonce', sa.Integer(),
    #               nullable=False, server_default='0'))

    conn = op.get_bind()
    conn.execute("PRAGMA legacy_alter_table=ON")
    # Save existing journalist table.
    op.rename_table("journalists", "journalists_tmp")

    # Add nonce column.
    op.add_column("journalists_tmp", sa.Column("session_nonce", sa.Integer()))

    # Populate nonce column.
    journalists = conn.execute(sa.text("SELECT * FROM journalists_tmp")).fetchall()

    for journalist in journalists:
        conn.execute(
            sa.text(
                """UPDATE journalists_tmp SET session_nonce=0 WHERE
                       id=:id"""
            ).bindparams(id=journalist.id)
        )

    # Now create new table with null constraint applied.
    op.create_table(
        "journalists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("pw_salt", sa.LargeBinary(), nullable=True),
        sa.Column("pw_hash", sa.LargeBinary(), nullable=True),
        sa.Column("passphrase_hash", sa.String(length=256), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("session_nonce", sa.Integer(), nullable=False),
        sa.Column("otp_secret", sa.String(length=32), nullable=True),
        sa.Column("is_totp", sa.Boolean(), nullable=True),
        sa.Column("hotp_counter", sa.Integer(), nullable=True),
        sa.Column("last_token", sa.String(length=6), nullable=True),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("last_access", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("uuid"),
    )

    conn.execute(
        """
        INSERT INTO journalists
        SELECT id, uuid, username, first_name, last_name, pw_salt, pw_hash,
               passphrase_hash, is_admin, session_nonce, otp_secret, is_totp,
               hotp_counter, last_token, created_on, last_access
        FROM journalists_tmp
    """
    )

    # Now delete the old table.
    op.drop_table("journalists_tmp")

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("journalist_id", sa.INTEGER(), nullable=False),
        sa.Column("token", sa.TEXT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["journalist_id"],
            ["journalists.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
