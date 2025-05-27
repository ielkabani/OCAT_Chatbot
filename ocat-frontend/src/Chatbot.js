import React, { useState, useRef, useEffect } from "react";
import { Container, Form, Button, Navbar } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Chatbot.css';

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const userMessage = { sender: "user", text: input };
    setMessages([...messages, userMessage]);
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          session_id: "default_session",
          history: messages.map(msg => ({
            sender: msg.sender,
            content: msg.text
          }))
        }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: data.response },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: "Error: Could not reach chatbot." },
      ]);
    }
    setInput("");
    setLoading(false);
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
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
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