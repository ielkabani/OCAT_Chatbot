import React, { useState, useRef, useEffect } from "react";
import { Container, Form, Button, Navbar } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Chatbot.css';

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Automatically focus the input field when the component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // New useEffect to focus input after bot replies (when loading becomes false)
  useEffect(() => {
    // Only focus if loading has just finished (is false)
    // and there are messages (meaning a send/receive cycle likely happened)
    // and the inputRef is available.
    // This prevents focusing on initial load if loading starts as false.
    if (!loading && messages.length > 0 && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading, messages]); // Re-run this effect when loading or messages change

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const userMessage = { sender: "user", text: input };
    // Update messages using a functional update to ensure we have the latest state
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Clear input immediately after capturing its value for the user message
    const currentInput = input;
    setInput(""); // Clear input sooner

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: currentInput, // Use the captured input
          session_id: "default_session",
          // Pass the most up-to-date messages state for history
          // Note: `messages` here might not include `userMessage` yet due to async nature of setMessages
          // For more accurate history, consider how `messages` state is managed or passed.
          // A common pattern is to build history from `prevMessages` if needed immediately.
          // However, for this specific focus issue, the current history mapping is likely okay.
          history: messages.map(msg => ({ // This `messages` is from the closure of sendMessage
            sender: msg.sender,
            content: msg.text
          }))
        }),
      });
      const data = await res.json();
      setMessages(prevMessages => [
        ...prevMessages,
        { sender: "bot", text: data.response },
      ]);
    } catch (err) {
      setMessages(prevMessages => [
        ...prevMessages,
        { sender: "bot", text: "Error: Could not reach chatbot." },
      ]);
    }
    // setInput(""); // Moved up to clear input sooner
    setLoading(false);
    // REMOVED: inputRef.current?.focus(); // This will be handled by the useEffect now
  };

  return (
    <div className="chat-container">
      <Navbar bg="white" className="chat-header">
        <Container>
          <Navbar.Brand>
            <img
              src="/logo.png"
              alt="OCAT Logo"
              className="logo"
            />
            OCAT Chatbot
          </Navbar.Brand>
        </Container>
      </Navbar>

      <div className="messages-container">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <Container>
          <Form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="d-flex gap-2"
          >
            <Form.Control
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()} // Check original input, not the potentially cleared one
            >
              Send
            </Button>
          </Form>
        </Container>
      </div>
    </div>
  );
}

export default Chatbot;