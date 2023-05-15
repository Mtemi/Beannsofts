from pandas import DataFrame
import talib.abstract as ta

from app.src.services.DCABot.strategy.strategy import IStrategy

class BollingerBand(IStrategy):
    def __init__(self, config):
        self.config = config
        super().__init__(config)

    def populateIndicator(self, dataframe: DataFrame) -> DataFrame:
        # RSI
        close = dataframe["close"]
        dataframe['bband_upper'] = ta.BBANDS(close, matype=0)
        dataframe['bband_lower'] = ta.BBANDS(close, matype=0)
        dataframe['bband_middle'] = ta.BBANDS(close, matype=0)

        return dataframe
    
    def populateBuyTrend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['bband_lower'] > dataframe['close']) 
            ),
            'buy'] = 1
        return dataframe
    
    def populateSellTrend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['bband_upper'] > dataframe['close']) 
            ),
            'sell'] = 1
        return dataframe
