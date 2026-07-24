"use client";

import { useEffect, useState } from "react";
import { Paper, Stack, Typography, Alert } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Users } from "lucide-react";
import { getSmeDirectory } from "@/lib/api";
import { SMEEntry } from "@/lib/types";

export default function SMEWidget() {
  const theme = useTheme();
  const [entries, setEntries] = useState<SMEEntry[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    getSmeDirectory()
      .then(setEntries)
      .catch(() => setError(true));
  }, []);

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
        height: "100%",
        minHeight: 0,
        overflow: "hidden",
        p: 2,
        borderRadius: 1.5,
      }}
    >
      <Stack direction="row" spacing={1} alignItems="center">
        <Users size={16} color={theme.palette.primary.main} />
        <Typography variant="subtitle2">Who knows what</Typography>
      </Stack>

      {error && (
        <Alert severity="info" variant="outlined" sx={{ fontSize: 12 }}>
          Backend not reachable yet — seed the DB and start the API.
        </Alert>
      )}

      <Stack spacing={1.5} sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {entries.map((e) => (
          <Paper key={e.author} variant="outlined" sx={{ p: 1.5, borderRadius: 1 }}>
            <Typography variant="body2" fontWeight={600}>
              {e.author}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 0.25, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: 0.5 }}
            >
              {e.domains.join(" · ")}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {e.document_count} documents
            </Typography>
          </Paper>
        ))}
      </Stack>
    </Paper>
  );
}
