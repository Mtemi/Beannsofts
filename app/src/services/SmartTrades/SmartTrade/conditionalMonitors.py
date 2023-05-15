"""
Smart TRADE conditonal monitors
@Param take profit(s)
@Param stop loss
@Param trailing stop
@Param trailing take profits
"""
from app.src.config import Config
import redis
import pickle

redis_store = Config.CELERY_BROKER_URL
conn = redis.StrictRedis('localhost')

def trailingBuyMonitor(exchangeData, currentPrice, trailingBuy):
    print('Checking the trailing Buy - SMART TRADE')

    state = {"on_target": False}
    exchange_id = exchangeData["exchange_id"]  # to be used as store key in redis broker
    symbol = exchangeData["symbol"]
    amount = float(exchangeData["amount"])
    trailingSet = trailingBuy["trailing_buy_price"]
    tempMarketPrice = float(currentPrice) # The current price now on binance at this instance
    trailingBuyTarget = float(trailingSet) #Percentage to trail order set price

    """
    initilalize a List in redis that will store the previous traillingPrice limit bound
        -  example - [trailingPrice, currentPrice]
        - Initially the list is None, has not stored any prices
    """
    priceComparisonList = conn.get(exchange_id)

    if priceComparisonList == None:
        # store the temp_market price in a redis store
        # Create and store the initial LIst on first run
        trailingBuyLimit = ((100 + trailingBuyTarget)/100) * tempMarketPrice

        priceComparisonList = [
            float(trailingBuyLimit), float(tempMarketPrice)]

        print("PRICE COMPARISON LIST", priceComparisonList)
        conn.set(exchange_id, pickle.dumps(priceComparisonList))
    else:
        #Finds the list is  not None , it loads the data to be examined
        priceComparisonList = pickle.loads(priceComparisonList)

    tempMarketPrice = priceComparisonList[1] #This is the precious market price in the previous n-1 check
    
    # Here we check if the currentPrice, in our case buy is below the previous marketPrice we are trailing(that is price N-1)
    if currentPrice < tempMarketPrice:
        """
            We check the percentage change in price, then we move the trailing sell limit with the same percentage
        """
        perc_market_change = (float((tempMarketPrice-currentPrice))/tempMarketPrice)*100
        # now move the trailingBuyLimit by the same percentage change
        trailingBuyLimit = ((100 - perc_market_change)/100) * \
            priceComparisonList[0]

        priceComparisonList[0] = float(trailingBuyLimit)
        priceComparisonList[1] = float(currentPrice)

        conn.set(exchange_id, pickle.dumps(priceComparisonList))

    # The price droppped and has closed the trailing Gap, so we trigger the order
    elif (currentPrice - priceComparisonList[0]) >= 0:
        print("[X] Trailing SELL reached. Sending order to binance ata [{0}].".format([priceComparisonList[0], currentPrice]))
        order_params = {'symbol': symbol, 'side': 'BUY'}
        order_params.update({"quantity": float(amount)})
        order_params.update({"type": "MARKET"})

        # place order using the order_data
        state.update({"on_target": True, "order_params": order_params})

        # lets delete the keyf from our redis database
        conn.delete(exchange_id)
    else:
        # Just update the current price
        priceComparisonList[1] = float(currentPrice)
        conn.set(exchange_id, pickle.dumps(priceComparisonList))
        print("[X] Trailig sell comparison list at [{0}].Still checking ...".format(priceComparisonList))
    return state

def takeProfitMonitor(exchange_data, current_price, take_profit_targets):
    """
    Comparing the price movement and the takeprofits params received 
    """
    state ={"on_target":False}
    take_profits = take_profit_targets["take_profits"]
    amount = exchange_data["amount"]
    symbol = exchange_data["symbol"]

    for takeprofit in take_profits:
        if  current_price<=float(takeprofit):
            order_params = {'symbol':symbol, 'side':'SELL'}
            amount_percent = take_profits[takeprofit]
            order_amount = (float(amount_percent)/100)*float(amount)
            # update params
            order_params.update({"quantity":order_amount})
            order_params.update({"type":take_profit_targets["take_profit_order_type"]})

            if take_profit_targets["take_profit_order_type"] == "LIMIT":
                order_params.update({"price":float(take_profit_targets["take_profit_price"]), "timeInForce":"GTC"})

            del take_profits[takeprofit]
            if len(take_profits) !=0:
                state.update({"on_target":True, "terminate_tp_checks":False, "order_params":order_params})
            else:
                state.update({"on_target":True, "terminate_tp_checks":True, "order_params":order_params})
            break
    return state
           
def stopLossMonitor(exchange_data, current_price, stop_loss_targets):
    state ={"on_target":False}
    stop_loss = float(stop_loss_targets["stop_loss"])
    amount = exchange_data["amount"]
    symbol = exchange_data["symbol"]

    if current_price <= stop_loss:
        order_params = {'symbol':symbol, 'side':'SELL'}
        order_params.update({"quantity":float(amount)})
        order_params.update({"type":stop_loss_targets["stop_loss_type"]})
        if stop_loss_targets["stop_loss_type"]=="LIMIT":
            order_params.update({"price":float(stop_loss_targets["stop_loss_price"]), "timeInForce":"GTC"})
        # place order using the order_data
        state.update({"on_target":True,"order_params":order_params})
    return state

def trailingStopLossMonitor(exchange_data,current_price, stop_loss_targets):

    # keep track on of the entry price
    # use more persistent memory prefer redis memory
    print('[X] Started checking the trailing stop')

    state ={"on_target":False}
    exchange_id = exchange_data["exchange_id"] #to be used as store key
    symbol = exchange_data["symbol"]
    amount = float(exchange_data["amount"])
    # temp_market_price = float(exchange_data["temp_market_price"])
    temp_market_price = float(current_price)
    trailing_stop_loss = float(stop_loss_targets["trailing_stop"])

    price_comparison_list = conn.get(exchange_id)
   
    if price_comparison_list ==None:
        # store the temp_market price in a redis store
        stop_loss_limit =((100 - trailing_stop_loss)/100)*temp_market_price

        price_comparison_list=[float(stop_loss_limit),float(temp_market_price)]
       
        
        conn.set(exchange_id, pickle.dumps(price_comparison_list))
    else:

        price_comparison_list = pickle.loads(price_comparison_list)
    
    temp_market_price = price_comparison_list[1]

    if current_price < temp_market_price:

        perc_market_change =(float((temp_market_price-current_price))/temp_market_price)*100
        # now move the stop_loss_limit by the same percentage change
        stop_loss_limit =((100 + perc_market_change)/100)*price_comparison_list[0]

        price_comparison_list[0] = float(stop_loss_limit)
        price_comparison_list[1] = float(current_price)

        conn.set(exchange_id, pickle.dumps(price_comparison_list))

    elif (current_price - price_comparison_list[0])>=0:

        print("[X] Trailing stop loss limit reached. Sending order to binance ata [{0}].".format([price_comparison_list[0],current_price]))
        order_params = {'symbol':symbol, 'side':'SELL'}
        order_params.update({"quantity":float(amount)})
        order_params.update({"type":stop_loss_targets["stop_loss_type"]})

        if stop_loss_targets["stop_loss_type"]=="LIMIT":
            order_params.update({"price":float(stop_loss_targets["stop_loss_price"]), "timeInForce":"GTC"})
        # place order using the order_data
        state.update({"on_target":True,"order_params":order_params})

        # lets delete the keyf from our redis database
        conn.delete(exchange_id)
    else:
        # Just update the current price
        price_comparison_list[1] = float(current_price)
        conn.set(exchange_id, pickle.dumps(price_comparison_list))
        print("[X] Trailig stop comparison list at [{0}].Still checking ...".format(price_comparison_list))
        
    return state
        
def trailingTakeProfitMonitor(exchange_data, current_price, take_profit_targets):
    # keep track on of the entry price
    # use more persistent memory prefer redis memory
    state ={"on_target":False}
    exchange_id = exchange_data["exchange_id"] #to be used as store key
    symbol = exchange_data["symbol"]
    amount = float(exchange_data["amount"])
    # temp_market_price = float(exchange_data["temp_market_price"])
    # temp_market_price = float(current_price)
    trailing_take_profit = float(take_profit_targets["trailing_take_profit"])
    for take_profit in take_profit_targets["take_profits"]:
    
        if current_price<=float(take_profit):
            print('[X] Started checking the trailing take profit')
            price_comparison_list = conn.get(exchange_id+'tp')
        
   
            if price_comparison_list ==None:
                # store the temp_market price in a redis store
                take_profit_limit =((100 - trailing_take_profit)/100)*float(take_profit)

                price_comparison_list=[float(take_profit_limit),float(take_profit)]
            
                
                conn.set(exchange_id+'tp', pickle.dumps(price_comparison_list))
            else:

                price_comparison_list = pickle.loads(price_comparison_list)
            
            temp_market_price = price_comparison_list[1]

            if current_price < temp_market_price:

                perc_market_change =(float((temp_market_price-current_price))/temp_market_price)*100
                # now move the stop_loss_limit by the same percentage change
                take_profit_limit =((100 + perc_market_change)/100)*price_comparison_list[0]

                price_comparison_list[0] = float(take_profit_limit)
                price_comparison_list[1] = float(current_price)

                conn.set(exchange_id+'tp', pickle.dumps(price_comparison_list))

            elif (current_price - price_comparison_list[0])>=0:

                print("[X] Trailing take profit limit reached. Sending order to binance ata [{0}].".format([price_comparison_list[0],current_price]))
                order_params = {'symbol':symbol, 'side':'SELL'}
                order_params.update({"quantity":float(amount)})
                order_params.update({"type":take_profit_targets["take_profit_order_type"]})

                if take_profit_targets["take_profit_order_type"]=="LIMIT":
                    order_params.update({"price":float(take_profit_targets["take_profit_price"]), "timeInForce":"GTC"})
                # place order using the order_data
                state.update({"on_target":True,"order_params":order_params})

                # lets delete the keyf from our redis database
                conn.delete(exchange_id+'tp')
            else:
                # Just update the current price
                price_comparison_list[1] = float(current_price)
                conn.set(exchange_id+'tp', pickle.dumps(price_comparison_list))
                print("[X] Trailig stop comparison list at [{0}].Still checking ...".format(price_comparison_list))
            break
        else:
            pass    
    return state