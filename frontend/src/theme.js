import { createTheme } from "@mui/material/styles";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#0D0D0D",
      paper: "#1E1E1E",
    },
    text: {
      primary: "#E4E4E4",
      secondary: "#8A8A8A",
    },
    primary: {
      main: "#166BE2",
    },
  },
  shape: {
    borderRadius: 8,
  },
});

export default darkTheme;
