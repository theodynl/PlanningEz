import { useEffect, useRef, useState } from "react";

export interface MenuItem {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  danger?: boolean;
  separator?: boolean;
  submenu?: MenuItem[];
}

interface Props {
  x: number;
  y: number;
  items: MenuItem[];
  onClose: () => void;
}

export function ContextMenu({ x, y, items, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [openSub, setOpenSub] = useState<number | null>(null);

  // Close on outside click or Escape.
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("mousedown", onDown);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  // Keep the menu within the viewport.
  const maxX = typeof window !== "undefined" ? window.innerWidth - 230 : x;
  const maxY = typeof window !== "undefined" ? window.innerHeight - 320 : y;

  const run = (item: MenuItem) => {
    if (item.disabled || item.submenu) return;
    item.onClick?.();
    onClose();
  };

  return (
    <div
      ref={ref}
      className="context-menu"
      style={{ left: Math.min(x, maxX), top: Math.min(y, maxY) }}
    >
      {items.map((item, i) =>
        item.separator ? (
          <div key={i} className="ctx-separator" />
        ) : (
          <div
            key={i}
            className={`ctx-item${item.disabled ? " disabled" : ""}${
              item.danger ? " danger" : ""
            }${item.submenu ? " has-sub" : ""}`}
            onMouseEnter={() => setOpenSub(item.submenu ? i : null)}
            onClick={() => run(item)}
          >
            <span>{item.label}</span>
            {item.submenu && <span className="ctx-arrow">▸</span>}
            {item.submenu && openSub === i && (
              <div className="context-submenu">
                {item.submenu.map((sub, j) => (
                  <div
                    key={j}
                    className={`ctx-item${sub.disabled ? " disabled" : ""}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!sub.disabled) {
                        sub.onClick?.();
                        onClose();
                      }
                    }}
                  >
                    {sub.label}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      )}
    </div>
  );
}
