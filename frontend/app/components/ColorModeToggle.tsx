"use client";

import { IconButton, Tooltip } from "@mui/material";
import { Sun, Moon } from "lucide-react";
import { useColorMode } from "@/app/ColorModeContext";

export default function ColorModeToggle() {
  const { mode, toggle } = useColorMode();

  return (
    <Tooltip title={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
      <IconButton onClick={toggle} size="small" sx={{ border: "1px solid", borderColor: "divider" }}>
        {mode === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </IconButton>
    </Tooltip>
  );
}
