import pickle
from pandas import DataFrame, to_datetime
from app.src.config import Config
from app.src.services.DCABot.strategy.StrategyResolver import StrategyResolver
from app.src.utils.binance.clientOriginal import Client as BinanceClient
import time
from typing import Dict, Optional, Tuple
from app.src.utils import logging
import arrow
from enum import Enum
from datetime import datetime, timezone, timedelta
import redis

logger = logging.GetLogger(__name__)

DEFAULT_DATAFRAME_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume','closetime', 'quoteassetvolume', 'noOftrades', 'takerbuybasevolume','takerbuyquotevolume', 'ignore']

class SignalType(Enum):
    """
    Enum to distinguish between buy and sell signals
    """
    BUY = "buy"
    SELL = "sell"

class SignalTagType(Enum):
    """
    Enum for signal columns
    """
    BUY_TAG = "buy_tag"

class DataProvider:
    def __init__(self, config: dict):
        self.exchange = BinanceClient()
        self.config = config
        self.pairListDataFrame: Dict[str, any] = {}
        self.strategy = StrategyResolver().loadStrategy(config['strategy'])
        self.ignore_buying_expired_candle_after: int = 0
        self.isActive = True
        self.redisConn = redis.from_url(Config.REDIS_URL)

    def timeFrameToMinutes(self, timeframe: str) -> int:
        amount = int(timeframe[0:-1])
        unit = timeframe[-1]
        if 'y' == unit:
            scale = 60 * 24 * 365
        elif 'M' == unit:
            scale = 60 * 24 * 30
        elif 'w' == unit:
            scale = 60 * 24 * 7
        elif 'd' == unit:
            scale = 60 * 24
        elif 'h' == unit:
            scale = 60
        elif 'm' == unit:
            scale = 1
        elif 's' == unit:
            scale = 1
        else:
            raise Exception('timeframe unit {} is not supported'.format(unit))
        return amount * scale

    def timeFrameToSeconds(self, timeframe: str) -> int:
        amount = int(timeframe[0:-1])
        unit = timeframe[-1]
        if 'y' == unit:
            scale = 60 * 60 * 24 * 365
        elif 'M' == unit:
            scale = 60 * 60 * 24 * 30
        elif 'w' == unit:
            scale = 60 * 60 * 24 * 7
        elif 'd' == unit:
            scale = 60 * 60 * 24
        elif 'h' == unit:
            scale = 60 * 60
        elif 'm' == unit:
            scale = 60
        elif 's' == unit:
            scale = 1
        else:
            raise Exception('timeframe unit {} is not supported'.format(unit))
        return amount * scale

    def ohlcv_fill_up_missing_data(self, dataframe: DataFrame, timeframe: str, pair: str) -> DataFrame:
        """
        Fills up missing data with 0 volume rows,
        using the previous close as price for "open", "high" "low" and "close", volume is set to 0
        """

        ohlcv_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        timeframe_minutes = self.timeFrameToMinutes(timeframe)
        logger.debug(f"Timeframe: {timeframe} in Minutes is: {timeframe_minutes}")

        # Resample to create "NAN" values
        df = dataframe.resample(f'{timeframe_minutes}min', on='date').agg(ohlcv_dict)

        # Forwardfill close for missing columns
        df['close'] = df['close'].fillna(method='ffill')
        # Use close for "open, high, low"
        df.loc[:, ['open', 'high', 'low']] = df[['open', 'high', 'low']].fillna(
            value={'open': df['close'],
                'high': df['close'],
                'low': df['close'],
                })
        df.reset_index(inplace=True)
        len_before = len(dataframe)
        len_after = len(df)
        pct_missing = (len_after - len_before) / len_before if len_before > 0 else 0
        if len_before != len_after:
            message = (f"Missing data fillup for {pair}: before: {len_before} - after: {len_after}"
                    f" - {round(pct_missing * 100, 2)}%")
            if pct_missing > 0.01:
                logger.debug(message)
            else:
                # Don't be verbose if only a small amount is missing
                logger.debug(message)
        # logger.debug(f"OHLCV after filling missing dataframe for {pair} @ {timeframe} and dataframe as {df}")
        return df

    def clean_ohlcv_dataframe(self, data: DataFrame, timeframe: str, pair: str, *,
                          fill_missing: bool = True,
                          drop_incomplete: bool = True) -> DataFrame:
        """
        Cleanse a OHLCV dataframe by
        * Grouping it by date (removes duplicate tics)
        * dropping last candles if requested
        * Filling up missing data (if requested)
        :param data: DataFrame containing candle (OHLCV) data.
        :param timeframe: timeframe (e.g. 5m). Used to fill up eventual missing data
        :param pair: Pair this data is for (used to warn if fillup was necessary)
        :param fill_missing: fill up missing candles with 0 candles
                            (see ohlcv_fill_up_missing_data for details)
        :param drop_incomplete: Drop the last candle of the dataframe, assuming it's incomplete
        :return: DataFrame
        """
        # group by index and aggregate results to eliminate duplicate ticks
        data = data.groupby(by='date', as_index=False, sort=True).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'max',
        })
        # eliminate partial candle
        # if drop_incomplete:
        #     data.drop(data.tail(1).index, inplace=True)

        # logger.debug(f"Datafrome before filling up missing data {data}")
        if fill_missing:
            return self.ohlcv_fill_up_missing_data(data, timeframe, pair)
        else:
            return data

    def ohlcvToDataframe(self, ohlcv: list, timeframe: str, pair: str, *,
                       fill_missing: bool = True, drop_incomplete: bool = True):
        """
        Converts a list with candle (OHLCV) data to a Dataframe
        :param ohlcv: list with candle (OHLCV) data, as returned by exchange.async_get_candle_history
        :param timeframe: timeframe (e.g. 5m). Used to fill up eventual missing data
        :param pair: Pair this data is for (used to warn if fillup was necessary)
        :param fill_missing: fill up missing candles with 0 candles
                            (see ohlcv_fill_up_missing_data for details)
        :param drop_incomplete: Drop the last candle of the dataframe, assuming it's incomplete
        :return: DataFrame
        """
        cols = DEFAULT_DATAFRAME_COLUMNS
        df = DataFrame(ohlcv, columns=cols)
        df["date"] = to_datetime(df["date"], unit="ms", utc=True, infer_datetime_format=True)

        df = df.astype(dtype={'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float',
                          'volume': 'float', 'closetime':'int', 'quoteassetvolume':'float',
                           'noOftrades':'int', 'takerbuybasevolume':'float', 'takerbuyquotevolume':'float', 'ignore':'float'})
        
        # logger.debug(f"Dataframe shape before cleaning: {df}")

        return self.clean_ohlcv_dataframe(df, timeframe, pair,
                                 fill_missing=fill_missing,
                                 drop_incomplete=drop_incomplete)

    def ohlcv(self, pair:str, timeframe:str):
        """
        Queries binance api to get the most recent candle stick data
        :param pair: Pair this data is for
        :param timeframe: timeframe (e.g 5m)
        :return DataFrame
        """
        logger.debug(f"Getting OHLCV for {pair} @ {timeframe}")
        # params = {
        #     "symbol": pair.upper(),
        #     "interval": timeframe
        # }
        # data =  self.exchange.get_klines(**params)
        # logger.debug(f"Raw kline data obtained from binance {data}")
        data = self.redisConn.lrange(f"{pair.lower()}@{timeframe}", 0, -1)
        # logger.debug(f"Raw kline data obtained from redis {data}")
        kline = []
        for klineData in data:
            kline.append(pickle.loads(klineData))
        # logger.debug(f"Raw kline data obtained from redis {kline}")
        return kline
        # return data
    
    def getPairDataframe(self, pair, timeframe = None) -> DataFrame:
        """
        Queries binance api to get the most recent candle stick data
        :param pair: Pair this data is for
        :param timeframe: timeframe (e.g 5m)
        :return DataFrame
        """
        klineData = self.ohlcv(pair, timeframe)
        dataframe = self.ohlcvToDataframe(klineData, timeframe, pair)
        logger.debug(f"Kline Dataframe obtained from binance for symbol {pair} @ timeframe {timeframe} AND DATAFRAME {dataframe}")
        return dataframe

    def reloadMarket(self) -> None:
        for pair in self.config['pairlist']:
            logger.debug(f"Reload markets for {pair}")
            dataframe = self.getPairDataframe(pair, self.config["timeframe"])
            logger.debug(f"Dataframe obtained from binance for symbol {pair} @ timeframe {self.config['timeframe']}")
            # logger.info(f"Dataframe obtained from reloadMarket {dataframe}")
            dframe = self.strategy.populateIndicator(self, dataframe)

            dataframe['buy'] = 0
            dataframe['sell'] = 0
            dataframe['buy_tag'] = 0
            logger.debug("Populating Buy and Sell signals")
            dframe = self.strategy.populateBuyTrend(self, dframe)
            dframe = self.strategy.populateSellTrend(self,dframe)
            self.pairListDataFrame.update({pair:dframe})

    def get_signal(self, pair: str, timeframe: str, dataframe: DataFrame) -> Tuple[bool, bool, Optional[str]]:
        """
        Calculates current signal based based on the buy / sell columns of the dataframe.
        Used by Bot to get the signal to buy or sell
        :param pair: pair in format ANTBTC
        :param timeframe: timeframe to use
        :param dataframe: Analyzed dataframe to get signal from.
        :return: (Buy, Sell) A bool-tuple indicating buy/sell signal
        """
        if not isinstance(dataframe, DataFrame) or dataframe.empty:
            logger.warning(f'Empty candle (OHLCV) data for pair {pair}')
            return False, False, None
        logger.warning(f"THE DATAFRAME TO BE USED IN get_signal {dataframe}")
        dataframe['date'].apply(lambda x:x.toordinal())
        latest_date = dataframe['date'].max()
        logger.debug(f"Latest date: {latest_date}")
        
        latest = dataframe.loc[dataframe['date'] == latest_date].iloc[-1]
        logger.debug(f"Latest candle dataframe: {latest}")

        # Explicitly convert to arrow object to ensure the below comparison does not fail
        latest_date = arrow.get(latest_date)
        
        # Check if dataframe is out of date
        timeframe_minutes = self.timeFrameToMinutes(timeframe)
        logger.debug(f'Checking if dataframe for pair {pair} is out of date, Timeframe: {timeframe}, timeframe in seconds: {timeframe_minutes}')
        offset = self.config.get('exchange', {}).get('outdated_offset', 5)
        logger.debug(f"OFFSET {offset}")
        buy, sell = False, False
        buy_tag = None
        logger.debug(f"BUY {sell}, SELL {sell}, BUY_TAG {buy_tag}")
        logger.debug(f"Latest date: {latest_date}")

        if latest_date < (arrow.utcnow().shift(minutes=-(timeframe_minutes * 2 + offset))):
            logger.warning(
                'Outdated history for pair %s. Last tick is %s minutes old',
                pair, int((arrow.utcnow() - latest_date).total_seconds() // 60)
            )
            return False, False, None
        # logger.debug(f"Latest buy: {latest['buy']}")
        if latest['buy'] == 1:  # buy signal
            logger.debug(f'Buy signal for pair {pair} triggered')
            return True, False, None

        if latest['sell'] == 1:  # sell signal
            logger.debug(f'Sell signal for pair {pair} triggered')
            return False, True, None

        logger.debug('trigger: %s (pair=%s) buy=%s sell=%s buy_tag=%s', latest['date'], pair, str(buy), str(sell), str(buy_tag))

        # buy = latest[SignalType.BUY.value] == 1
        # logger.debug(f"GENERATED BUY {buy}")
        # sell = False
        # if SignalType.SELL.value in latest:
        #     sell = latest[SignalType.SELL.value] == 1

        # buy_tag = latest.get(SignalTagType.BUY_TAG.value, None)

        # logger.debug('trigger: %s (pair=%s) buy=%s sell=%s buy_tag=%s',
        #              latest['date'], pair, str(buy), str(sell), str(buy_tag))
        
        timeframe_seconds = self.timeFrameToSeconds(timeframe)
        if self.ignore_expired_candle(latest_date=latest_date,
                                      current_time=datetime.now(timezone.utc),
                                      timeframe_seconds=timeframe_seconds,
                                      buy=buy):
            return False, sell, buy_tag

        logger.debug(f"End of get signal method")
        
        # TODO Return this to buy
        return buy, sell, buy_tag

    def ignore_expired_candle(self, latest_date: datetime, current_time: datetime,
                              timeframe_seconds: int, buy: bool):
        if self.ignore_buying_expired_candle_after and buy:
            time_delta = current_time - (latest_date + timedelta(seconds=timeframe_seconds))
            return time_delta.total_seconds() > self.ignore_buying_expired_candle_after
        else:
            return False
    
    def getAnalyzedDataframe(self, pair: str,timeframe: str) -> DataFrame:
        """
        Gets the analyzed dataframe for a pair
        :param pair: pair to get dataframe for
        :param timeframe: timeframe to use
        :return: DataFrame
        """
        if pair not in self.pairListDataFrame:
            self.pairListDataFrame[pair] = self.getPairDataframe(pair, timeframe)
        return self.pairListDataFrame[pair]