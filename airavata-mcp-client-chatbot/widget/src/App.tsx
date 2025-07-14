import React from "react";
import Chatbox from "./components/Chatbox";

const App: React.FC = () => {
  return (
    <div
      style={{
        height: "100vh",
        backgroundColor: "#f5f5f5",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "20px",
        textAlign: "center", // optional for centering heading text
      }}
    >
      <h1>What can I do for your research?</h1>
      <Chatbox />
    </div>
  );
};

export default App;
