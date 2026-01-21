import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export default function HamburgerMenu() {
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);
    const buttonRef = useRef(null);
    const { i18n, t } = useTranslation();

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target) &&
                buttonRef.current &&
                !buttonRef.current.contains(event.target)
            ) {
                setMenuOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const changeLanguage = (lng) => {
        i18n.changeLanguage(lng);

        const root = document.documentElement;
        root.classList.remove('lang-urdu', 'lang-english', 'lang-roman');

        if (lng === 'ur') root.classList.add('lang-urdu', 'urdu');
        else if (lng === 'roman') root.classList.add('lang-roman', 'roman');
        else root.classList.add('lang-english', 'english');
    };

    const changeFontSize = (size) => {
        const root = document.documentElement;
        root.classList.remove('font-small', 'font-medium', 'font-large');
        root.classList.add(`font-${size}`);
    };

    const changeTheme = (theme) => {
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
            >
                ☰
            </button>

            {menuOpen && (
                <div className="menu-dropdown" ref={menuRef}>
                    <div className="menu-section">
                        <h3>{t('language')}</h3>
                        <button onClick={() => changeLanguage('en')}>English</button>
                        <button onClick={() => changeLanguage('ur')}>اردو</button>
                        <button onClick={() => changeLanguage('roman')}>Roman</button>
                    </div>

                    <div className="menu-section">
                        <h3>{t('fontSize')}</h3>
                        <button onClick={() => changeFontSize('small')}>{t('small')}</button>
                        <button onClick={() => changeFontSize('medium')}>{t('medium')}</button>
                        <button onClick={() => changeFontSize('large')}>{t('large')}</button>
                    </div>

                    <div className="menu-section">
                        <h3>{t('theme')}</h3>
                        <button onClick={() => changeTheme('light')}>{t('light')}</button>
                        <button onClick={() => changeTheme('dark')}>{t('dark')}</button>
                    </div>
                </div>
            )}
        </div>
    );
}
