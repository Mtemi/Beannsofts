from app.src.services.DCABot.strategy.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
from app.src.utils import logging   

logger = logging.GetLogger(__name__)
class RSI(IStrategy):
    def __init__(self, config):
        self.config = config
        super().__init__(config)

    def populateIndicator(self, dataframe: DataFrame) -> DataFrame:
        # RSI
        period = int(self.config['timeframe'][0:-1])
        print(f"Period Timeframe from Indicator {period}")
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=period)
        # print("Populated timeframe data from RSI strategy Indicator {}".format(dataframe))
        return dataframe
    
    def populateBuyTrend(self, dataframe: DataFrame) -> DataFrame:
        # get the current candle
        current_candle = dataframe.iloc[-1].squeeze()

        # if RSI greater than 70 and profit is positive, then sell
        if (current_candle['rsi'] < 30):
            dataframe['buy'] = 1
   
        # dataframe.loc[ (current_candle['rsi'] <= 30),'buy'] = 1
        print(f"Obtained dataframe with buy trend indicator")
        return dataframe

    def populateSellTrend(self, dataframe: DataFrame) -> DataFrame:
         # get the current candle
        current_candle = dataframe.iloc[-1].squeeze()
      
        # if RSI greater than 70 and profit is positive, then sell
        if (current_candle['rsi'] >= 70):
            dataframe['sell'] = 1
            logger.info(f"Obtained dataframe with sell trend indicator")
            return dataframe
    
        return dataframe