"use client";

import { Box, ButtonBase, Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { PersonaKey, PERSONAS } from "@/lib/types";
import { ShieldCheck } from "lucide-react";

interface Props {
  active: PersonaKey;
  onSwitch: (persona: PersonaKey) => void;
}

/**
 * The signature element of this UI: an ID-badge card, swapped like a
 * physical badge when judges switch identities. The colored stripe encodes
 * the persona's highest-privilege role — the same tag that gates retrieval
 * on the backend, made visible instead of hidden.
 */
export default function PersonaSwitcher({ active, onSwitch }: Props) {
  const theme = useTheme();
  const roleColor = theme.palette.roleColors;

  return (
    <Stack direction="row" spacing={1.5}>
      {(Object.keys(PERSONAS) as PersonaKey[]).map((key) => {
        const persona = PERSONAS[key];
        const isActive = key === active;
        const primaryRole = persona.roles[0];
        return (
          <ButtonBase
            key={key}
            onClick={() => onSwitch(key)}
            aria-pressed={isActive}
            sx={{
              width: 224,
              display: "flex",
              alignItems: "stretch",
              borderRadius: 1.5,
              overflow: "hidden",
              textAlign: "left",
              border: "1px solid",
              borderColor: isActive ? "primary.main" : "divider",
              boxShadow: isActive ? `0 0 0 1px ${theme.palette.primary.main}66` : "none",
              opacity: isActive ? 1 : 0.5,
              transition: "all 0.15s ease",
              "&:hover": { opacity: isActive ? 1 : 0.9 },
            }}
          >
            <Box sx={{ width: 6, flexShrink: 0, bgcolor: roleColor[primaryRole as keyof typeof roleColor] ?? roleColor.dev }} />
            <Stack sx={{ flex: 1, bgcolor: "background.paper", px: 1.5, py: 1, gap: 0.25 }}>
              <Typography
                variant="caption"
                sx={{ fontFamily: "var(--font-mono)", fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5 }}
                color="text.secondary"
              >
                {isActive ? "Active badge" : "Switch to"}
              </Typography>
              <Typography variant="subtitle2" sx={{ lineHeight: 1.2 }}>
                {persona.displayName}
              </Typography>
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
  );
}
