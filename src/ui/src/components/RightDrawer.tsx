/*
Module: 6. User Interface
Author: Forked
Date: 2026-01-20
Purpose: Provides the rightdrawer module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { useCallback, useContext, useEffect, type PropsWithChildren } from "react";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Drawer from "@mui/material/Drawer";
import { useTheme, useMediaQuery } from "@mui/material";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import { isTabOrShift, type InteractionEvent } from "../utils/events";

import Hidden from "./Hidden";
import { store } from "../store";
import ACTIONS from "../actions";

import "./RightDrawer.scss";

export default function RightDrawer( { children, inlineOnDesktop = false }: PropsWithChildren & { inlineOnDesktop?: boolean } ) {
  const { state, dispatch } = useContext(store);
  const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const openRightDrawer = useCallback(
    (event: InteractionEvent) => {
      if (isTabOrShift(event)) {
        return;
      }

      dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: true });
    },
    [dispatch]
  );

  const closeRightDrawer = useCallback(
    (event: InteractionEvent) => {
      if (isTabOrShift(event)) {
        return;
      }

      dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: false });
    },
    [dispatch]
  );

  // If we switch into mobile, ensure right drawer is closed and never rendered on mobile.
  useEffect(() => {
    if (isMobile && state.isRightDrawerOpen) {
      dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: false });
    }
  }, [isMobile, state.isRightDrawerOpen, dispatch]);

  return (
    <>
      {/* Do not render any right-drawer UI on mobile (right drawer is disabled on small screens). */}
      {!isMobile && !inlineOnDesktop && (
        <Drawer
          className="right-drawer"
          anchor="right"
          variant="persistent"
          open={state.isRightDrawerOpen}
        >
          <div className="drawer-content" style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
            {/* Close button at top for desktop persistent drawer */}
            <div style={{ display: "flex", justifyContent: "flex-end", padding: 6 }}>
              <IconButton
                aria-label="Close analysis"
                onClick={() => dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: false })}
                size="small"
                sx={{ color: "white" }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </div>
            {children}
          </div>
        </Drawer>
      )}
    </>
  );
}
