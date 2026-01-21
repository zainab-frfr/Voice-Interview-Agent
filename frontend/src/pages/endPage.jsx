import { useTranslation } from 'react-i18next';
import HamburgerMenu from "../components/hamburgerMenu";


export default function EndPage() {
  const { t } = useTranslation(); 


  
 
  
  return (
    <div className="landing-container">
      <HamburgerMenu />
      
      <div className="content-center">
        <h1>{t("end_message")}</h1>
        
      </div>
    </div>
  );
}