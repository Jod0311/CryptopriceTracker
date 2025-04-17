import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


def train_model(df, coin_symbol):
    coin_df = df[df['symbol'] == coin_symbol].copy()
    coin_df = coin_df.sort_index()

    coin_df['timestamp'] = coin_df.index.astype('int64') // 10**9 # convert to seconds

    X = coin_df[['timestamp']]
    y = coin_df['current_price']

    if len(X) < 5:
        return None, None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = LinearRegression()
    model.fit(X_train, y_train)

    return model, X_test.iloc[-1].values[0]
