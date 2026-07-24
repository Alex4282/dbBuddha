"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Stack, Typography, Chip, IconButton, Tooltip, CircularProgress } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { BrainCircuit, LogOut } from "lucide-react";
import PersonaSwitcher from "@/app/components/PersonaSwitcher";
import ChatInterface from "@/app/components/ChatInterface";
import AppDomainSidebar from "@/app/components/AppDomainSidebar";
import SMEWidget from "@/app/components/SMEWidget";
import ColorModeToggle from "@/app/components/ColorModeToggle";
import { PersonaKey } from "@/lib/types";
import { getSession, setSession, clearSession } from "@/lib/session";

export default function DashboardPage() {
  const router = useRouter();
  const theme = useTheme();
  const [persona, setPersona] = useState<PersonaKey | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    setPersona(session.persona);
    setChecking(false);
  }, [router]);

  function handleSwitch(next: PersonaKey) {
    setPersona(next);
    const session = getSession();
    if (session) setSession({ ...session, persona: next });
  }

  function handleLogout() {
    clearSession();
    router.replace("/login");
  }

  if (checking || !persona) {
    return (
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <CircularProgress size={24} sx={{ color: "primary.main" }} />
      </Box>
    );
  }

  return (
    <Box sx={{ mx: "auto", display: "flex", height: "100vh", maxWidth: "1400px", flexDirection: "column", gap: 2, p: 2 }}>
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ pb: 2, borderBottom: "1px solid", borderColor: "divider" }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <BrainCircuit size={22} color={theme.palette.primary.main} />
          <Typography variant="h6">NexusMind</Typography>
          <Chip
            label="need-to-know onboarding"
            size="small"
            variant="outlined"
            sx={{ ml: 1, fontFamily: "var(--font-mono)", fontSize: 10, color: "text.secondary" }}
          />
        </Stack>

        <Stack direction="row" spacing={2} alignItems="center">
          <PersonaSwitcher active={persona} onSwitch={handleSwitch} />
          <ColorModeToggle />
          <Tooltip title="Log out">
            <IconButton onClick={handleLogout} size="small" sx={{ border: "1px solid", borderColor: "divider" }}>
              <LogOut size={16} />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      <Box
        sx={{
          flex: 1,
          overflow: "hidden",
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "220px 1fr 260px" },
        }}
      >
        <AppDomainSidebar />
        <ChatInterface persona={persona} />
        <SMEWidget />
      </Box>
    </Box>
  );
}
