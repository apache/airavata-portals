import React, { useState } from 'react';

function Chatbox() {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() === '') return;
    console.log('Send message:', input);
    setInput('');
  };

  const styles = {
    inputContainer: {
      borderRadius: 25,
      background: '#FFF',
      boxShadow: '0px 3px 13.3px rgba(0, 0, 0, 0.25)',
      width: 890,
      height: 100,
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      marginTop: 20,
    },
    input: {
      flex: 1,
      height: '60%',
      border: 'none',
      fontSize: 16,
      outline: 'none',
    },
    button: {
      padding: '10px 20px',
      marginLeft: 10,
      borderRadius: 20,
      border: 'none',
      backgroundColor: '#007bff',
      color: '#fff',
      cursor: 'pointer',
    },
  };

  return (
    <div style={styles.inputContainer}>
      <input
        type="text"
        placeholder="Ask away :)"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={styles.input}
      />
      <button onClick={handleSend} style={styles.button}>
        Send
      </button>
    </div>
  );
}

export default Chatbox;
