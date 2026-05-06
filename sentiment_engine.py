from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def get_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of the given text and return sentiment scores.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing 'neg', 'neu', 'pos', and 'compound' scores.
    """
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)

# Example usage:
if __name__ == "__main__":
    sample_text = "I love this product! It's amazing and works perfectly."
    sentiment = get_sentiment(sample_text)
    print(f"Text: {sample_text}")
    print(f"Sentiment: {sentiment}")