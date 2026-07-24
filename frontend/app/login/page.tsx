"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Paper,
  Stack,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  ButtonBase,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { BrainCircuit, ShieldCheck, LogIn } from "lucide-react";
import { getPersonaToken } from "@/lib/api";
import { setSession } from "@/lib/session";
import { PersonaKey, PERSONAS } from "@/lib/types";
import ColorModeToggle from "@/app/components/ColorModeToggle";

export default function LoginPage() {
  const router = useRouter();
  const theme = useTheme();
  const roleColor = theme.palette.roleColors;
  const [selected, setSelected] = useState<PersonaKey>("junior_dev");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignIn() {
    setLoading(true);
    setError(null);
    try {
      const token = await getPersonaToken(selected);
      setSession({ token, persona: selected });
      router.push("/");
    } catch (err) {
      setError("Couldn't reach NexusMind. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box
      sx={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        backgroundImage:
          "radial-gradient(circle at 50% 0%, rgba(201,161,92,0.08), transparent 60%)",
      }}
    >
      <Box sx={{ position: "absolute", top: 16, right: 16 }}>
        <ColorModeToggle />
      </Box>

      <Paper sx={{ width: "100%", maxWidth: 420, p: 4, borderRadius: 2 }}>
        <Stack spacing={0.5} alignItems="center" sx={{ mb: 3 }}>
          <BrainCircuit size={28} color={theme.palette.primary.main} />
          <Typography variant="h5">NexusMind</Typography>
          <Chip
            label="need-to-know onboarding"
            size="small"
            variant="outlined"
            sx={{ fontFamily: "var(--font-mono)", color: "text.secondary", mt: 1 }}
          />
        </Stack>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, textAlign: "center" }}>
          Choose an identity badge to sign in. This is a demo login — no password
          required — the badge you pick determines exactly what the assistant is
          allowed to retrieve for you.
        </Typography>

        <Stack spacing={1.5} sx={{ mb: 3 }}>
          {(Object.keys(PERSONAS) as PersonaKey[]).map((key) => {
            const persona = PERSONAS[key];
            const isActive = key === selected;
            const primaryRole = persona.roles[0];
            return (
              <ButtonBase
                key={key}
                onClick={() => setSelected(key)}
                sx={{
                  display: "flex",
                  alignItems: "stretch",
                  borderRadius: 1.5,
                  overflow: "hidden",
                  textAlign: "left",
                  border: "1px solid",
                  borderColor: isActive ? "primary.main" : "divider",
                  boxShadow: isActive ? `0 0 0 1px ${theme.palette.primary.main}66` : "none",
                  opacity: isActive ? 1 : 0.7,
                  transition: "all 0.15s ease",
                }}
              >
                <Box sx={{ width: 6, flexShrink: 0, bgcolor: roleColor[primaryRole as keyof typeof roleColor] ?? roleColor.dev }} />
                <Stack sx={{ flex: 1, px: 2, py: 1.5, gap: 0.25 }}>
                  <Typography variant="subtitle2">{persona.displayName}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {persona.title}
                  </Typography>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    alignItems="center"
                    sx={{ mt: 0.5, color: "primary.main", fontFamily: "var(--font-mono)", fontSize: 10 }}
                  >
                    <ShieldCheck size={11} />
                    <span>{persona.roles.join(" · ")}</span>
                  </Stack>
                </Stack>
              </ButtonBase>
            );
          })}
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <ButtonBase
          onClick={handleSignIn}
          disabled={loading}
          sx={{
            width: "100%",
            py: 1.25,
            borderRadius: 1.5,
            bgcolor: "primary.main",
            color: "primary.contrastText",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 1,
            "&:hover": { filter: "brightness(1.1)" },
            "&.Mui-disabled": { opacity: 0.6 },
          }}
        >
          {loading ? <CircularProgress size={16} color="inherit" /> : <LogIn size={16} />}
          Sign in as {PERSONAS[selected].displayName}
        </ButtonBase>
      </Paper>
    </Box>
  );
}
