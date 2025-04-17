import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


def train_model(df, coin_symbol):
    coin_df = df[df['symbol'] == coin_symbol].copy()
    coin_df = coin_df.sort_index()

    coin_df['timestamp'] = coin_df.index.astype('int64') // 10**9

    required_features = ['timestamp', 'open', 'high', 'low', 'volume', 'market_cap']
    for feature in required_features:
        if feature not in coin_df.columns:
            return None, None

    coin_df.dropna(subset=required_features + ['current_price'], inplace=True)

    if len(coin_df) < 5:
        return None, None

    X = coin_df[required_features]
    y = coin_df['current_price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = LinearRegression()
    model.fit(X_train, y_train)

    return model, X_test.iloc[-1].values.reshape(1, -1)
