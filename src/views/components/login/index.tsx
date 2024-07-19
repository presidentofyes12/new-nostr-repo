import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import { nip06, getPublicKey } from 'nostr-tools';

import { InstallNip07Dialog } from 'views/components/dialogs/no-wallet/nip07';
import ImportAccount from 'views/components/dialogs/import-account';
import useMediaBreakPoint from 'hooks/use-media-break-point';
import useTranslation from 'hooks/use-translation';
import useModal from 'hooks/use-modal';
import {
  keysAtom,
  profileAtom,
  backupWarnAtom,
  ravenAtom,
  ravenStatusAtom,
} from 'atoms';
import Creation from 'svg/creation';
import Import from 'svg/import';
import { storeKeys } from 'local-storage';
import { Keys } from 'types';
import * as React from 'react';
import Typography from '@mui/material/Typography';
import Modal from '@mui/material/Modal';
import DownloadSeedWords from 'views/settings/DownloadSeedWords';
import { Checkbox } from '@mui/material';
import { CiWarning } from 'react-icons/ci';
import { IoMdClose } from 'react-icons/io';
import LoginMetadataForm from '../metadata-form/loginForm';

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '700px',
  maxWidth: '100%',
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

const Login = (props: { onDone: () => void }) => {
  const { onDone } = props;
  const { isSm } = useMediaBreakPoint();
  const [t] = useTranslation();
  const [, showModal] = useModal();
  const [, setKeys] = useAtom(keysAtom);
  const [profile, setProfile] = useAtom(profileAtom);
  const [, setBackupWarn] = useAtom(backupWarnAtom);
  const [raven] = useAtom(ravenAtom);
  const [ravenStatus] = useAtom(ravenStatusAtom);
  const [step, setStep] = useState<0 | 1 | 2>(0);

  useEffect(() => {
    if (step === 1 && ravenStatus.ready) setStep(2);
  }, [step, ravenStatus.ready]);

  useEffect(() => {
    if (profile) onDone();
  }, [profile]);

  const [seedWords, setSeedWords] = React.useState('');
  const [priv, setPriv] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [understand, setUnderstand] = React.useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const createAccount = () => {
    const seedWords = nip06.generateSeedWords();
    const priv = nip06.privateKeyFromSeedWords(seedWords);
    setSeedWords(seedWords);
    setPriv(priv);
    localStorage.setItem('seedWords', seedWords);
    handleOpen();
  };

  const continueCreateAccount = (priv: any) => {
    handleClose();
    loginPriv(priv);
    setBackupWarn(true);
  };
  const importAccount = () => {
    showModal({
      body: (
        <ImportAccount
          onSuccess={(key, type) => {
            showModal(null);
            if (type === 'priv') {
              loginPriv(key);
            } else if (type === 'pub') {
              proceed({ priv: 'none', pub: key });
            }
          }}
        />
      ),
    });
  };

  const loginNip07 = async () => {
    if (!window.nostr) {
      showModal({
        body: <InstallNip07Dialog />,
      });
      return;
    }

    const pub = await window.nostr.getPublicKey();
    if (pub) proceed({ priv: 'nip07', pub });
  };

  const loginPriv = (priv: string) => {
    const pub = getPublicKey(priv);
    proceed({ priv, pub });
  };

  const proceed = (keys: Keys) => {
    storeKeys(keys).then(() => {
      setKeys(keys);
      setProfile(null);
      if (keys?.priv === 'none') {
        onDone();
        return;
      }
      setStep(1);
    });
  };

  return (
    <>
      <div>
        <Modal
          open={open}
          // onClose={handleClose}
          aria-labelledby="modal-modal-title"
          aria-describedby="modal-modal-description"
        >
          <Box sx={style}>
            <Typography id="modal-modal-title" variant="h6" component="h2">
              <div className="flex_2s">
                <span>
                  <CiWarning /> Important
                </span>
                <span
                  onClick={e => handleClose()}
                  style={{ cursor: 'pointer' }}
                >
                  <IoMdClose />
                </span>
              </div>
            </Typography>
            <Typography id="modal-modal-description" sx={{ mt: 2, mb: 2 }}>
              Your mnemonic seed phrase will be display under your  profile
              (Once you Logged in ) . Please ensure now to Download it and  keep it safe as it is
              crucial for recovering your account if needed.
            </Typography>
            <p>
              <Checkbox onChange={e => setUnderstand(!understand)} />
              <span>
                I Understand and i will keep mnemonic seed phrase save and
                secure !
              </span>
            </p>
            {understand ? (
              <div className="flex_2s">
                  <DownloadSeedWords
                    text={seedWords}
                    title="Download Seed Phrase "
                  /> 
                <button
                  className="btn btn_primary"
                  onClick={e => continueCreateAccount(priv)}
                >
                  Next
                </button>
              </div>
            ) : (
              ''
            )}
          </Box>
        </Modal>
      </div>

      <Box
        component="img"
        src="/logo-large-white.png"
        sx={{
          width: isSm ? '526px' : '100%',
          height: isSm ? '132px' : null,
          m: '20px 0 10px 0',
        }}
      />
      <Divider sx={{ m: '28px 0' }} />
      {(() => {
        if (step === 1) {
          return (
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <CircularProgress />
            </Box>
          );
        }

        if (step === 2) {
          return (
            <>
              <LoginMetadataForm
                skipButton={<Button onClick={onDone}>{t('Skip')}</Button>}
                submitBtnLabel={t('Create Account')}
                onSubmit={data => {
                  raven?.updateProfile(data).then(() => onDone());
                }}
              />
            </>
          );
        }

        return (
          <>
            <Box sx={{ color: 'text.secondary', mb: '28px' }}>
              {t('Sign in to get started')}
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexDirection: isSm ? 'row' : 'column',
              }}
            >
              <Button
                variant="login"
                size="large"
                disableElevation
                fullWidth
                onClick={createAccount}
                sx={{
                  mb: '22px',
                  p: '20px 26px',
                  mr: isSm ? '22px' : null,
                }}
                startIcon={<Creation width={38} />}
              >
                {t('Create Nostr Account')}
              </Button>
              <Button
                variant="login"
                size="large"
                disableElevation
                fullWidth
                onClick={importAccount}
                sx={{ mb: '22px', p: '20px 26px' }}
                startIcon={<Import width={38} />}
              >
                {t('Import Nostr Account')}
              </Button>
            </Box>
          </>
        );
      })()}
    </>
  );
};

export default Login;
