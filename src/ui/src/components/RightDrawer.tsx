import { useCallback, useContext, type PropsWithChildren } from "react";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Drawer from "@mui/material/Drawer";
import { isTabOrShift, type InteractionEvent } from "../utils/events";

import Hidden from "./Hidden";
import { store } from "../store";
import ACTIONS from "../actions";

import "./RightDrawer.scss";

export default function RightDrawer( { children, inlineOnDesktop = false }: PropsWithChildren & { inlineOnDesktop?: boolean } ) {
  const { state, dispatch } = useContext(store);
  const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

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

  return (
    <>
      <Hidden breakpoint={{ size: "lg", direction: "up" }} implementation="js">
        <SwipeableDrawer
          className="right-drawer"
          anchor="right"
          open={state.isRightDrawerOpen}
          onClose={closeRightDrawer}
          onOpen={openRightDrawer}
          disableBackdropTransition={!iOS}
          disableDiscovery={iOS}
          onKeyDown={closeRightDrawer}
        >
          <div className="drawer-content">
            {children}
          </div>
        </SwipeableDrawer>
      </Hidden>
      {/* On desktop, render the permanent Drawer only when not using inline box */}
      {!inlineOnDesktop && (
        <Hidden breakpoint={{ size: "md", direction: "down" }} implementation="css">
          <Drawer
            className="right-drawer"
            anchor="right"
            variant="permanent"
            open
          >
            <div className="drawer-content">
              {children}
            </div>
          </Drawer>
        </Hidden>
      )}
    </>
  );
}
