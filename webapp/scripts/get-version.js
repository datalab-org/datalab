#!/usr/bin/env node
// This script tries to get the version of the app from three sources:
//
// 1. The VITE_APP_GIT_VERSION environment variable
// 2. The latest git tag
// 3. The version field in package.JSON
//
// It can be used as part of the build system to set the
// `VITE_APP_GIT_VERSION` environment variable itself.

const { execSync } = require("child_process");
const fs = require("fs");

function getPackageJsonVersion() {
  try {
    const packageJson = JSON.parse(fs.readFileSync("package.json", "utf8"));
    return packageJson.version || "unknown";
  } catch (error) {
    console.error("Error reading package.json:", error);
    return "unknown";
  }
}

function getGitVersion() {
  try {
    const tag = execSync("git describe --tags").toString().trim();
    return tag;
  } catch (error) {
    console.error("Error getting git version:", error);
    return null;
  }
}

function getVersion() {
  // Check if VITE_APP_GIT_VERSION is already set (e.g., by build system)
  if (process.env.VITE_APP_GIT_VERSION) {
    return process.env.VITE_APP_GIT_VERSION;
  }

  // Try to get git version
  const gitVersion = getGitVersion();
  if (gitVersion) {
    return gitVersion;
  }

  // Fall back to package.json version
  return getPackageJsonVersion();
}

// Get and log the version
const version = getVersion();
console.log(version);
