"use client";

import { Paper, Stack, Typography, List, ListItemButton, ListItemText, Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Boxes, KeyRound } from "lucide-react";

const DOMAINS = [
  { name: "Payment Gateway", services: ["payment-svc", "ledger-svc", "helm charts"] },
  { name: "Auth Service", services: ["token issuer", "userinfo API", "session store"] },
];

export default function AppDomainSidebar() {
  const theme = useTheme();

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        height: "100%",
        minHeight: 0,
        overflow: "hidden",
        p: 2,
        borderRadius: 1.5,
      }}
    >
      <Stack direction="row" spacing={1} alignItems="center">
        <Boxes size={16} color={theme.palette.primary.main} />
        <Typography variant="subtitle2">Domains</Typography>
      </Stack>

      <Stack spacing={2} component="nav" sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {DOMAINS.map((domain) => (
          <Box key={domain.name}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mb: 0.5, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: 0.5 }}
            >
              {domain.name}
            </Typography>
            <List dense disablePadding>
              {domain.services.map((s) => (
                <ListItemButton key={s} sx={{ borderRadius: 1, py: 0.5 }}>
                  <ListItemText primaryTypographyProps={{ variant: "body2" }} primary={s} />
                </ListItemButton>
              ))}
            </List>
          </Box>
        ))}
      </Stack>

      <Stack
        direction="row"
        spacing={1}
        sx={{ mt: "auto", p: 1.5, borderRadius: 1.5, border: "1px solid", borderColor: "divider" }}
      >
        <KeyRound size={14} color={theme.palette.primary.main} style={{ marginTop: 2, flexShrink: 0 }} />
        <Typography variant="caption" color="text.secondary">
          Every answer is filtered by your badge&rsquo;s roles and groups before it ever reaches the model.
        </Typography>
      </Stack>
    </Paper>
  );
}
