/*
Module: 6. User Interface
Author: Forked
Date: 2025-11-16
Purpose: Provides the events module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { type KeyboardEvent } from "react";

export type InteractionEvent =
  | React.KeyboardEvent
  | React.MouseEvent
  | React.TouchEvent;
type KeydownEvent = React.KeyboardEvent & { type: "keydown" };

export const isKeyDownEvent = (
  event: InteractionEvent
): event is KeydownEvent => event && event.type === "keydown";

export const isTabOrShift = (event: InteractionEvent) =>
  isKeyDownEvent(event) && (event.key === "Tab" || event.key === "Shift");

export function allowOnlyNumberKeys(e: KeyboardEvent<HTMLInputElement>) {
  const allowedKeys = [
    "Backspace",
    "ArrowLeft",
    "ArrowRight",
    "Delete",
    "Tab",
    "Enter",
  ];

  if (!/[0-9]/.test(e.key) && !allowedKeys.includes(e.key)) {
    e.preventDefault();
  }
}
