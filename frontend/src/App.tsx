import React, { useState, useEffect } from "react";

const App: React.FC = () => {
  const [instagramLink, setInstagramLink] = useState<string>("");
  const [result, setResult] = useState<string | null>(null); // store model result
  const [error, setError] = useState<string | null>(null); // store error messages

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInstagramLink(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!instagramLink.trim()) {
      setError("Oops! Looks like the link is missing. \nPlease enter an Instagram link.");
      setResult(null);
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/filter?post_id=${encodeURIComponent(instagramLink)}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Flask should return: { "general_sentiment": "positive" }
      setResult(`The General Sentiment is: ${data.general_sentiment}`);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch sentiment. Please try again.");
      setResult(null);
    }

    setInstagramLink(""); // clear input
  };

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("");
      }, 5000); // 5 seconds
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (result) {
      const timer = setTimeout(() => {
        setResult("");
      }, 60000); // 1 minute
      return () => clearTimeout(timer);
    }
  }, [result]);

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Instagram Comment Analysis</h1>
      <h2>Paste an Instagram link to analyze comment sentiment.</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          type="text"
          placeholder="Please paste the Instagram link here"
          value={instagramLink}
          onChange={handleInputChange}
          style={styles.input}
        />

        {error && <div style={styles.error}>{error}</div>}

        <button type="submit" style={styles.button}>
          Submit
        </button>

        {result && (
          <div style={{ marginTop: "20px", fontSize: "18px", fontWeight: "bold" }}>
            {result}
          </div>
        )}
      </form>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    width: "100vw",
    fontFamily: "'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif",
    background: "linear-gradient(160deg, #e6f2ff, #cce6ff, #99ccff)",
    color: "#1a3d6d",
  },

  header: {
    fontFamily: "'Playfair Display', serif",
    fontSize: "55px",
    fontWeight: 700,
    marginBottom: "20px",
    textAlign: "center",
    color: "#1a3d6d",
  },

  form: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: "100%",
    maxWidth: "700px",
    padding: "20px",
    backgroundColor: "white",
    borderRadius: "12px",
    boxShadow: "0 6px 18px rgba(0, 0, 0, 0.1)",
  },
  input: {
    padding: "12px",
    marginBottom: "15px",
    borderRadius: "8px",
    border: "1px solid #99c2ff",
    fontSize: "16px",
    outline: "none",
    transition: "border-color 0.3s ease",
    width: "95%",
  },
  button: {
    padding: "12px",
    marginTop: "5px",
    backgroundColor: "#3399ff", // tech blue
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "background-color 0.3s ease",
    width: "30%",
  },
  buttonHover: {
    backgroundColor: "#267fd9", // darker blue on hover
  },
  error: {
    color: "#aa0000ff",
    fontSize: "15px",
    fontWeight: 500,
    marginBottom: "10px",
    textAlign: "center",
  },
};

export default App;
