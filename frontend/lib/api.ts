import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 30000,
});

export interface TickerSummary {
  ticker:     string;
  last_close: number;
  change_pct: number;
  volume:     number;
  rsi:        number;
  trend:      string;
}

export interface OHLCVPoint {
  time:   string;
  open:   number;
  high:   number;
  low:    number;
  close:  number;
  volume: number;
}

export interface PredictResponse {
  ticker:          string;
  prediction:      string;
  confidence:      number;
  lstm_proba:      number;
  sentiment_score: number;
  recommendation:  string;
}

export interface BacktestResult {
  ticker:         string;
  model_return:   number;
  buyhold_return: number;
  sharpe:         number;
  max_drawdown:   number;
  win_rate:       number;
  total_trades:   number;
}

export interface BacktestSummary {
  avg_model_return:   number;
  avg_buyhold_return: number;
  avg_sharpe:         number;
  avg_max_drawdown:   number;
  best_ticker:        string;
  worst_ticker:       string;
  outperform_count:   number;
  total_tickers:      number;
}

export const marketAPI = {
  getTickers:   () => api.get<{tickers: string[]}>("/market/tickers"),
  getSummary:   () => api.get<TickerSummary[]>("/market/summary"),
  getOHLCV:     (ticker: string, limit = 100) =>
    api.get<OHLCVPoint[]>(`/market/ohlcv/${ticker}?limit=${limit}`),
};

export const predictAPI = {
  predict: (ticker: string, news_text = "market neutral") =>
    api.post<PredictResponse>("/predict/", { ticker, news_text }),
};

export const sentimentAPI = {
  analyze: (text: string) =>
    api.post("/sentiment/", { text }),
};

export const backtestAPI = {
  getResults: () => api.get<BacktestResult[]>("/backtest/results"),
  getSummary: () => api.get<BacktestSummary>("/backtest/summary"),
};

export default api;