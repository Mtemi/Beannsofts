"""roll back

Revision ID: 7d6f840fdda3
Revises: 
Create Date: 2023-04-22 12:49:02.674909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d6f840fdda3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subscription_plans',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan', sa.String(length=50), nullable=False),
    sa.Column('features', sa.PickleType(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('price', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plan')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('registered_on', sa.DateTime(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('telegram_token', sa.String(length=80), nullable=False),
    sa.Column('telegram_id', sa.String(length=80), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('exchange',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('exchange_name', sa.String(length=50), nullable=False),
    sa.Column('key', sa.String(length=255), nullable=False),
    sa.Column('secret', sa.String(length=255), nullable=False),
    sa.Column('exchange_type', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('exchange_name')
    )
    op.create_table('invoices',
    sa.Column('invoice_id', sa.String(length=50), nullable=False),
    sa.Column('invoice_code', sa.String(length=50), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('invoice_status', sa.String(length=50), nullable=False),
    sa.Column('plan', sa.String(length=50), nullable=True),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('plan_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('invoice_id')
    )
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('expiry_date', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('plan_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bot',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('botName', sa.String(length=50), nullable=False),
    sa.Column('symbol', sa.String(length=50), nullable=False),
    sa.Column('baseSymbol', sa.String(length=50), nullable=True),
    sa.Column('side', sa.String(length=50), nullable=True),
    sa.Column('orderType', sa.String(length=50), nullable=True),
    sa.Column('tradeAmt', sa.Float(), nullable=False),
    sa.Column('interval', sa.Integer(), nullable=True),
    sa.Column('maxTradeCounts', sa.Integer(), nullable=True),
    sa.Column('maxOrderAmt', sa.Float(), nullable=True),
    sa.Column('minOrderAmt', sa.Float(), nullable=True),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('takeProfit', sa.Integer(), nullable=True),
    sa.Column('stopLoss', sa.Integer(), nullable=True),
    sa.Column('trailingStop', sa.Integer(), nullable=True),
    sa.Column('callbackRate', sa.Float(), nullable=True),
    sa.Column('leverage', sa.Integer(), nullable=True),
    sa.Column('signalType', sa.String(length=50), nullable=True),
    sa.Column('botStatus', sa.Boolean(), nullable=False),
    sa.Column('botType', sa.String(length=50), nullable=False),
    sa.Column('task_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('exchange_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('botName')
    )
    op.create_table('dca_bot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('botname', sa.String(length=255), nullable=False),
    sa.Column('botType', sa.String(), nullable=False),
    sa.Column('side', sa.String(length=50), nullable=True),
    sa.Column('pairlist', sa.PickleType(), nullable=False),
    sa.Column('ordertype', sa.String(length=50), nullable=True),
    sa.Column('qty', sa.Integer(), nullable=False),
    sa.Column('leverage', sa.Integer(), nullable=True),
    sa.Column('stoploss', sa.Float(), nullable=True),
    sa.Column('takeprofit', sa.Float(), nullable=True),
    sa.Column('trailing_stop', sa.Float(), nullable=True),
    sa.Column('trailing_stop_enabled', sa.Boolean(), nullable=True),
    sa.Column('strategy', sa.String(length=255), nullable=False),
    sa.Column('timeframe', sa.String(length=255), nullable=False),
    sa.Column('interval_between_orders', sa.Integer(), nullable=True),
    sa.Column('order_timeout', sa.Integer(), nullable=True),
    sa.Column('max_active_trade_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('is_running', sa.Boolean(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('stopped_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('task_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('exchange_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('grid_bot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('botName', sa.String(length=50), nullable=True),
    sa.Column('botType', sa.String(length=50), nullable=False),
    sa.Column('symbol', sa.String(length=50), nullable=True),
    sa.Column('gridQty', sa.Integer(), nullable=True),
    sa.Column('maxTradeCounts', sa.Integer(), nullable=True),
    sa.Column('upperLimitPrice', sa.Float(), nullable=True),
    sa.Column('lowerLimitPrice', sa.Float(), nullable=True),
    sa.Column('qtyPerGrid', sa.Float(), nullable=True),
    sa.Column('gridPoints', sa.PickleType(), nullable=True),
    sa.Column('exchange_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('is_running', sa.Boolean(), nullable=False),
    sa.Column('task_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('smart_orders_model',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('smart_order_type', sa.String(length=25), nullable=False),
    sa.Column('exchange_id', sa.BigInteger(), nullable=False),
    sa.Column('exchange_order_id', sa.BigInteger(), nullable=False),
    sa.Column('sl_steps', sa.BigInteger(), nullable=False),
    sa.Column('userid', sa.BigInteger(), nullable=False),
    sa.Column('task_id', sa.String(length=255), nullable=True),
    sa.Column('symbol', sa.String(length=25), nullable=False),
    sa.Column('side', sa.String(), nullable=False),
    sa.Column('amt', sa.Float(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('order_details_json', sa.PickleType(), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=255), nullable=False),
    sa.Column('executed_on', sa.DateTime(), nullable=True),
    sa.Column('change_reason', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ),
    sa.ForeignKeyConstraint(['userid'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('terminal_trades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exchange_id', sa.BigInteger(), nullable=False),
    sa.Column('userid', sa.BigInteger(), nullable=False),
    sa.Column('symbol', sa.String(length=25), nullable=False),
    sa.Column('side', sa.String(), nullable=False),
    sa.Column('type', sa.String(length=25), nullable=False),
    sa.Column('unit', sa.Float(), nullable=False),
    sa.Column('amt', sa.Float(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('timeinforce', sa.String(length=25), nullable=True),
    sa.Column('leverage', sa.Integer(), nullable=True),
    sa.Column('targetprice', sa.Float(), nullable=True),
    sa.Column('triggerprice', sa.Float(), nullable=True),
    sa.Column('timeout', sa.Integer(), nullable=True),
    sa.Column('trailing', sa.Float(), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=255), nullable=False),
    sa.Column('executed_on', sa.DateTime(), nullable=True),
    sa.Column('change_reason', sa.String(length=255), nullable=True),
    sa.Column('taskid', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ),
    sa.ForeignKeyConstraint(['userid'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dca_orders',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('order_id', sa.BigInteger(), nullable=True),
    sa.Column('bot_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('symbol', sa.String(length=50), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('order_type', sa.String(length=50), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('leverage', sa.Integer(), nullable=True),
    sa.Column('side', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('is_open', sa.Boolean(), nullable=False),
    sa.Column('filled_amt', sa.Float(), nullable=True),
    sa.Column('remaining_amt', sa.Float(), nullable=True),
    sa.Column('order_date', sa.DateTime(), nullable=True),
    sa.Column('order_filled_date', sa.DateTime(), nullable=True),
    sa.Column('order_update_date', sa.DateTime(), nullable=True),
    sa.Column('order_timeout', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bot_id'], ['dca_bot.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('binance_order_id', sa.BigInteger(), nullable=False),
    sa.Column('symbol', sa.String(length=50), nullable=False),
    sa.Column('clientOrderId', sa.String(length=50), nullable=True),
    sa.Column('transactTime', sa.BigInteger(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('origQty', sa.Float(), nullable=True),
    sa.Column('executedQty', sa.Float(), nullable=True),
    sa.Column('cummulativeQuoteQty', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('timeInForce', sa.String(length=50), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('side', sa.String(length=50), nullable=True),
    sa.Column('fills', sa.PickleType(), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('avgPrice', sa.Float(), nullable=True),
    sa.Column('cumQty', sa.Float(), nullable=True),
    sa.Column('cumQuote', sa.Float(), nullable=True),
    sa.Column('reduceOnly', sa.Boolean(), nullable=True),
    sa.Column('closePosition', sa.Boolean(), nullable=True),
    sa.Column('positionSide', sa.String(length=50), nullable=True),
    sa.Column('stopPrice', sa.Float(), nullable=True),
    sa.Column('workingType', sa.String(length=50), nullable=True),
    sa.Column('priceProtect', sa.Boolean(), nullable=True),
    sa.Column('origType', sa.String(length=50), nullable=True),
    sa.Column('updateTime', sa.BigInteger(), nullable=True),
    sa.Column('exchange_type', sa.String(length=50), nullable=True),
    sa.Column('bot_id', sa.BigInteger(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('orders')
    op.drop_table('dca_orders')
    op.drop_table('terminal_trades')
    op.drop_table('smart_orders_model')
    op.drop_table('grid_bot')
    op.drop_table('dca_bot')
    op.drop_table('bot')
    op.drop_table('subscriptions')
    op.drop_table('invoices')
    op.drop_table('exchange')
    op.drop_table('users')
    op.drop_table('subscription_plans')
    # ### end Alembic commands ###