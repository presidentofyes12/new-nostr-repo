import React from 'react';

const DownloadSeedWords: React.FC<{ text: string , title:string }> = ({ text , title }) => {
  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([text], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'nostrSeedWords.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    window.localStorage.setItem("downloaded", "true")
  };

  return (
    <button className='btn btn_success'  onClick={handleDownload}>
      {title ? title:'Download Seed Words'}
    </button>
  );
};

export default DownloadSeedWords;
