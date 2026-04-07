/*
Module: 6. User Interface
Author: Forked
Date: 2025-11-30
Purpose: Provides the numerictextinput module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { TextField } from "@mui/material";
import React from "react";
import { allowOnlyNumberKeys } from "../utils/events";

import "./NumericTextInput.scss"

type NumericTextInputProps = Omit<
  React.ComponentProps<typeof TextField>, "onChange"
> & {
  value: string;
  onChange: (value: string) => void;
  onCommit?: () => void;
};

export default function NumericTextInput({
  value,
  onChange,
  onCommit,
  ...props
}: NumericTextInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    allowOnlyNumberKeys(e);
    if (e.key === "Enter") {
      e.preventDefault();
      onCommit?.();
    }
  };

  return (
    <TextField
      {...props}
      className="numeric-textfield"
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={handleKeyDown}
      onBlur={onCommit}
    />
  );
}
