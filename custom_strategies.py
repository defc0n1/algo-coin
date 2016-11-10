import pandas
from datetime import datetime
from strategy import ticks, NullTradingStrategy
import matplotlib.pyplot as plt
import seaborn as sns


class SMACrossesStrategy(NullTradingStrategy):
    def __init__(self, size_short, size_long):
        super(SMACrossesStrategy, self).__init__()

        self.short = size_short
        self.shorts = []
        self.short_av = 0

        self.long = size_long
        self.longs = []
        self.long_av = []

        self.prev_state = ''
        self.state = ''

        self.bought = 0.0
        self.profits = 0.0

        self._intitialvalue = 0.0
        self._portfoliovalue = []

    def onBuy(self, data):
        if self._intitialvalue == 0.0:
            try:
                date = datetime.fromtimestamp(float(data['time']))
            except ValueError:
                date = datetime.strptime(data['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            self._intitialvalue = (
                date,
                float(data['price'])
                )
            self._portfoliovalue.append(self._intitialvalue)

        self.bought = float(data['price'])
        # print('d->g:bought at', self.bought)

    def onSell(self, data):
        profit = float(data['price']) - self.bought
        self.profits += profit
        # print('g->d:sold at',
        #       float(data['price']),
        #       profit,
        #       self.profits)
        self.bought = 0.0

        try:
            date = datetime.fromtimestamp(float(data['time']))
        except ValueError:
            date = datetime.strptime(data['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        self._portfoliovalue.append((
                date,
                self._portfoliovalue[-1][1] + profit))

    @ticks
    def onMatch(self, data):
        self.shorts.append(float(data['price']))
        self.longs.append(float(data['price']))

        if len(self.shorts) > self.short:
            self.shorts.pop(0)

        if len(self.longs) > self.long:
            self.longs.pop(0)

        self.short_av = float(sum(self.shorts)) / max(len(self.shorts), 1)
        self.long_av = float(sum(self.longs)) / max(len(self.longs), 1)

        self.prev_state = self.state
        if self.short_av > self.long_av:
            self.state = 'golden'
        elif self.short_av < self.long_av:
            self.state = 'death'
        else:
            self.state = ''

        if len(self.longs) < self.long or len(self.shorts) < self.short:
            return False

        if self.state == 'golden' and self.prev_state != 'golden' and \
                self.bought == 0.0:  # watch for floating point error
            self.requestBuy(self.onBuy, data)
            return True

        elif self.state == 'death' and self.prev_state != 'death' and \
                self.bought > 0.0:
            self.requestSell(self.onSell, data)
            return True

        return False

    def onAnalyze(self, _):
        # pd = pandas.DataFrame(self._actions,
        #                       columns=['time', 'action', 'price'])
        pd = pandas.DataFrame(self._portfoliovalue,
                              columns=['time', 'value'])
        pd.set_index(['time'], inplace=True)
        print(pd)

        sp500 = pandas.DataFrame()
        tmp = pandas.read_csv('./data/sp/sp500_v_kraken.csv')
        sp500['Date'] = pandas.to_datetime(tmp['Date'])
        sp500['Close'] = tmp['Close']
        sp500.set_index(['Date'], inplace=True)
        print(sp500)

        sns.set_style('darkgrid')
        fig, ax1 = plt.subplots()

        plt.title('BTC mean-rev algo 1 performance')
        ax1.plot(pd)

        ax1.set_ylabel('Portfolio value($)')
        ax1.set_xlabel('Date')
        for xy in [self._portfoliovalue[0]] + [self._portfoliovalue[-1]]:
            ax1.annotate('$%s' % xy[1], xy=xy, textcoords='data')

        # ax2 = ax1.twinx()
        # ax2.plot(sp500, 'r')
        # ax2.set_ylabel('S&P500 ($)')
        plt.show()