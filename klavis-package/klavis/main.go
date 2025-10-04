package main

import (
	"fmt"
	"klavis/commands"

	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "klavis",
		Short: "Klavis CLI tool",
	}

	rootCmd.AddCommand(commands.GetInstallCommand())
	rootCmd.AddCommand(commands.GetRunCommand())
	rootCmd.AddCommand(commands.GetListCommand())
	rootCmd.AddCommand(commands.GetUninstallCommand())
	rootCmd.AddCommand(commands.GetSearchCommand())

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
	}
}
