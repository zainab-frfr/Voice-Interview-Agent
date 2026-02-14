'use client';

import { useState, useRef, useEffect } from 'react';

export function HamburgerMenu() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !(menuRef.current as HTMLElement).contains(event.target as Node) &&
        buttonRef.current &&
        !(buttonRef.current as HTMLElement).contains(event.target as Node)
      ) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const changeLanguage = (lng: string) => {
    const root = document.documentElement;
    root.classList.remove('lang-urdu', 'lang-english', 'lang-roman');
    root.classList.remove('urdu', 'english', 'roman');

    if (lng === 'ur') {
      root.classList.add('lang-urdu', 'urdu');
    } else if (lng === 'roman') {
      root.classList.add('lang-roman', 'roman');
    } else {
      root.classList.add('lang-english', 'english');
    }
  };

  const changeFontSize = (size: string) => {
    const root = document.documentElement;
    root.classList.remove('font-small', 'font-medium', 'font-large');
    root.classList.add(`font-${size}`);
  };

  const changeTheme = (theme: string) => {
    const root = document.documentElement;
    root.classList.remove('light-mode', 'dark-mode');
    root.classList.add(`${theme}-mode`);
  };

  return (
    <div className="hamburger-menu">
      <button
        ref={buttonRef}
        className="hamburger-button"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Menu"
      >
        ☰
      </button>

      {menuOpen && (
        <div className="menu-dropdown" ref={menuRef}>
          <div className="menu-section">
            <h3>Language</h3>
            <button onClick={() => changeLanguage('en')}>English</button>
            <button onClick={() => changeLanguage('ur')}>اردو</button>
            <button onClick={() => changeLanguage('roman')}>Roman</button>
          </div>

          <div className="menu-section">
            <h3>Font Size</h3>
            <button onClick={() => changeFontSize('small')}>Small</button>
            <button onClick={() => changeFontSize('medium')}>Medium</button>
            <button onClick={() => changeFontSize('large')}>Large</button>
          </div>

          <div className="menu-section">
            <h3>Theme</h3>
            <button onClick={() => changeTheme('light')}>Light</button>
            <button onClick={() => changeTheme('dark')}>Dark</button>
          </div>
        </div>
      )}
    </div>
  );
}