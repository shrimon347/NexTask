import type { TypedUseSelectorHook } from "react-redux";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "./store";

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

export const selectSidebarOpenState = (state: RootState) => {
    const s = state.sidebar;

    return s.isOpen || (s.settings.isHoverOpen && s.isHover);
};
