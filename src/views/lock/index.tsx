import React, { useEffect, useState } from "react";
import { Link, RouteComponentProps, useNavigate } from "@reach/router";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import { Helmet } from "react-helmet";
import useMediaBreakPoint from "hooks/use-media-break-point";
import useTranslation from "hooks/use-translation";
import { toast } from "react-toastify";
import { FaLockOpen } from "react-icons/fa";

const LockPage = (_: RouteComponentProps) => {
  const { isSm } = useMediaBreakPoint();
  const [isAccountExist, setIsAccountExist] = useState(false);
  const [isAccountLoading, setIsAccountLoading] = useState(true);
  const [password, setPassword] = useState("");
  const [userName, setUserName] = useState("");
  const [enteredPassword, setEnteredPassword] = useState("");
  const [t] = useTranslation();

  useEffect(() => {
    const storedPassword = window.localStorage.getItem("password");
    if (storedPassword) {
      setIsAccountExist(true);
      setPassword(storedPassword);
    } else {
      setIsAccountExist(false);
    }
    setIsAccountLoading(false);
  }, []);

  const handleCreateAccount = () => {
    window.localStorage.setItem("username", userName);
    window.localStorage.setItem("password", password);
    window.localStorage.setItem("initLock", "initLock");
    setIsAccountExist(true);
  };

  const handleLogin = () => {
    const storedPassword = window.localStorage.getItem("password");

    if (enteredPassword === storedPassword) {
      window.localStorage.setItem("auth", "true");
      window.location.href = "/home";
    } else {
      // Username or password is incorrect
      toast("Invalid username or password. Please try again.");
    }
  };

  if (isAccountLoading) {
    return <div>Loading...</div>;
  }

  const handleReset = () => {
    const result = window.confirm("Are you sure  ? To reset your password ? ");
    if (result) {
      window.localStorage.removeItem("username");
      window.localStorage.removeItem("password");
      window.localStorage.removeItem("initLock");
      window.localStorage.removeItem("keys")
      window.localStorage.removeItem("auth")
      window.location.href="/login"
    }
  };
  return (
    <>
      <Helmet>
        <title>{t("Locked")}</title>
      </Helmet>
      <Box sx={{ width: isSm ? "590px" : "96%" }}>
        <Card sx={{ p: "26px 32px 46px 32px" }} className="auth_form">
          {isAccountExist ? (
            <>
              <h4 className="text-center">UnLock Screen</h4>
              <div>
                <div>
                  <input
                    type="password"
                    placeholder="Enter password"
                    value={enteredPassword}
                    onChange={(e) => setEnteredPassword(e.target.value)}
                  />
                  <button
                    className="mr-3 btn btn_success"
                    onClick={handleLogin}
                  >
                    <span className="mr-2">
                      <FaLockOpen />
                    </span>
                    UnLock
                  </button>
                  <button
                    onClick={(e) => handleReset()}
                    className=" btn btn_success"
                  >
                    Account Reset by Nsec{" "}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <>
              {window.localStorage.getItem("keys") ? (
                <>
                  <h4 className="text-center">Setup Password</h4>
                  <div>
                    <input
                      className="form-control"
                      type="text"
                      placeholder="Enter username"
                      value={userName}
                      onChange={(e) => setUserName(e.target.value)}
                    />
                    <input
                      className="form-control"
                      type="password"
                      placeholder="Enter password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                      className="btn btn_success mt-3 mr-3"
                      onClick={handleCreateAccount}
                    >
                      Setup Password
                    </button>
                    <Link to="/login">
                      <button className="btn btn_primary mt-3 mr-3">
                        Create/Import Account
                      </button>
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  <h4 className="text-center">No Account Founded </h4>
                  <p>
                    Please login to Nostr Account and Setup Password at first{" "}
                  </p>
                  <div>
                    <Link to="/login">
                      <button className="btn btn_primary mt-3 mr-3">
                        Create/Import Account
                      </button>
                    </Link>
                  </div>
                </>
              )}
            </>
          )}
        </Card>
      </Box>
    </>
  );
};

export default LockPage;
