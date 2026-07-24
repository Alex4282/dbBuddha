"use client";

import { useEffect, useRef, useState } from "react";
import {
  Box,
  Paper,
  Stack,
  Typography,
  TextField,
  Button,
  Chip,
  LinearProgress,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Send, Link2, Gauge, ShieldOff } from "lucide-react";
import { getPersonaToken, queryKnowledgeBase } from "@/lib/api";
import { ChatMessage, PersonaKey, PERSONAS } from "@/lib/types";

interface Props {
  persona: PersonaKey;
}

function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ fontFamily: "var(--font-mono)", fontSize: 10 }} color="text.secondary">
      <Gauge size={11} />
      <Box sx={{ width: 64, height: 4, borderRadius: 999, overflow: "hidden", bgcolor: "divider" }}>
        <LinearProgress
          variant="determinate"
          value={pct}
          sx={{ height: "100%", bgcolor: "transparent", "& .MuiLinearProgress-bar": { bgcolor: "primary.main" } }}
        />
      </Box>
      <span>{pct}% match</span>
    </Stack>
  );
}

function AssistantBubble({ message }: { message: ChatMessage }) {
  const theme = useTheme();
  const roleColor: Record<string, string> = {
    Jira: theme.palette.roleColors.dev,
    Confluence: theme.palette.roleColors.management,
    Teams: theme.palette.roleColors.hr,
    GitHub: theme.palette.roleColors.admin,
  };

  if (message.accessDenied) {
    return (
      <Paper
        className="redaction-stripe"
        sx={{ maxWidth: 560, p: 2, borderRadius: 1.5, borderColor: "error.main", overflow: "hidden" }}
      >
        <Stack direction="row" spacing={1} alignItems="center" className="animate-stamp" color="error.main">
          <ShieldOff size={16} />
          <Typography variant="subtitle2" sx={{ textTransform: "uppercase", letterSpacing: 0.5, color: "inherit" }}>
            Access denied
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {message.content}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ maxWidth: 560, p: 2, borderRadius: 1.5 }}>
      <Stack spacing={1.5}>
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
          {message.content}
        </Typography>

        {message.sources && message.sources.length > 0 && (
          <Stack direction="row" flexWrap="wrap" gap={1} sx={{ pt: 1.5, borderTop: "1px solid", borderColor: "divider" }}>
            {message.sources.map((s, i) => (
              <Chip
                key={i}
                component="a"
                href={s.source_url}
                target="_blank"
                rel="noreferrer"
                clickable
                icon={<Link2 size={10} />}
                label={`${s.source_type} · ${s.title}`}
                variant="outlined"
                size="small"
                sx={{ color: roleColor[s.source_type] ?? "text.secondary", borderColor: "divider" }}
              />
            ))}
          </Stack>
        )}

        {typeof message.confidence === "number" && <ConfidenceGauge value={message.confidence} />}
      </Stack>
    </Paper>
  );
}

export default function ChatInterface({ persona }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Re-mint identity whenever the demo persona switches — this is the only
  // thing that changes; the query logic below is identical for every user.
  useEffect(() => {
    getPersonaToken(persona).then(setToken).catch(console.error);
  }, [persona]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const query = input.trim();
    if (!query || !token || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: query }]);
    setLoading(true);

    try {
      // NOTE: for a real "streaming" experience, replace this with an SSE
      // endpoint backed by Anthropic/OpenAI's streaming API and append
      // tokens as they arrive; kept as a single awaited call here to keep
      // the hackathon scaffold small.
      const result = await queryKnowledgeBase(query, token);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          confidence: result.confidence,
          accessDenied: result.access_denied,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Something went wrong reaching NexusMind. Is the backend running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        borderRadius: 1.5,
        bgcolor: "background.default",
        overflow: "hidden",
      }}
    >
      <Box sx={{ px: 2, py: 1.5, borderBottom: "1px solid", borderColor: "divider" }}>
        <Typography variant="subtitle2">Ask NexusMind</Typography>
        <Typography variant="caption" color="text.secondary">
          Answering as <Box component="span" sx={{ color: "primary.main" }}>{PERSONAS[persona].displayName}</Box> ·{" "}
          {PERSONAS[persona].title}
        </Typography>
      </Box>

      <Stack spacing={2} sx={{ flex: 1, minHeight: 0, overflowY: "auto", p: 2 }}>
        {messages.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            Try: &ldquo;How do I run the auth service locally?&rdquo; or &ldquo;What are the rules for Q3 salary
            increases?&rdquo;
          </Typography>
        )}
        {messages.map((m) =>
          m.role === "user" ? (
            <Box
              key={m.id}
              sx={{
                ml: "auto",
                maxWidth: 560,
                borderRadius: 1.5,
                bgcolor: "divider",
                px: 2,
                py: 1,
                fontSize: 14,
              }}
            >
              {m.content}
            </Box>
          ) : (
            <AssistantBubble key={m.id} message={m} />
          )
        )}
        {loading && (
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "var(--font-mono)" }}>
            NexusMind is retrieving eligible context…
          </Typography>
        )}
        <div ref={scrollRef} />
      </Stack>

      <Stack direction="row" spacing={1} sx={{ p: 1.5, borderTop: "1px solid", borderColor: "divider" }}>
        <TextField
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about deployments, services, or team knowledge…"
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          disabled={loading}
          startIcon={<Send size={14} />}
        >
          Send
        </Button>
      </Stack>
    </Paper>
  );
}
