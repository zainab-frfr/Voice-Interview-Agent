import { useTranslation } from 'react-i18next';
import HamburgerMenu from "../components/hamburgerMenu";
import { useNavigate } from 'react-router-dom';


export default function LandingPage() {
  const { t } = useTranslation(); 

  const navigate = useNavigate();
  
  const startInterview = () => {
    localStorage.setItem("user_interacted", "true");
    navigate('/interview');
  };
  
  
  return (
    <div className="landing-container">
      <HamburgerMenu />
      
      <div className="content-center">
        <h1>{t("welcome_message")}</h1>
        <button className="start-button" onClick={startInterview}>
          {t("start_interview_button")}
        </button>
      </div>
    </div>
  );
}