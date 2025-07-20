# Research Group Post-Install Script

A robust, safe, and interactive post-installation script for Ubuntu 24.04 LTS designed for research groups. This script helps set up essential software packages with proper state tracking, rollback capabilities, and comprehensive logging.

## Features

### ✅ Core Capabilities
- **Pure Python**: No external dependencies required
- **Idempotent**: Safe to run multiple times
- **State Tracking**: Maintains installation history in JSON format
- **Rollback Support**: Can undo previous installations
- **Dry Run Mode**: Preview changes without executing
- **Interactive Mode**: User-guided software selection
- **Comprehensive Logging**: Detailed logs with configurable verbosity
- **Category-based Installation**: Organized software packages by purpose

### 🛡️ Safety Features
- **Error Handling**: Graceful failure recovery
- **Command Validation**: Checks for command availability before execution
- **Installation Tracking**: Records success/failure of each package
- **Rollback Capability**: Undo installations if needed
- **Dry Run Testing**: Preview all actions before execution

## Software Categories

### Essential (`essential`)
- **curl**: Data transfer tool
- **wget**: Web downloader  
- **git**: Version control system
- **vim**: Text editor
- **htop**: System monitor
- **tree**: Directory tree viewer
- **zip/unzip**: Archive utilities

### Development (`development`)
- **build-essential**: Compilation tools
- **cmake**: Build system
- **nodejs/npm**: Node.js runtime
- **docker**: Container platform
- **code**: VS Code editor (via snap)

### Python (`python`)
- **python3-dev**: Python development headers
- **python3-pip**: Python package installer
- **uv**: Fast Python package manager (custom install)
- **poetry**: Python dependency management (custom install)
- **pipx**: Install Python apps in isolation

### Research (`research`)
- **r-base**: R statistical computing
- **texlive**: LaTeX document system
- **pandoc**: Document converter

### Multimedia (`multimedia`)
- **ffmpeg**: Multimedia framework
- **imagemagick**: Image manipulation
- **vlc**: Media player (via snap)

### Productivity (`productivity`)
- **firefox**: Web browser (via snap)
- **libreoffice**: Office suite (via snap)
- **thunderbird**: Email client (via snap)

## Usage Examples

### Basic Installation
```bash
# Install essential software only (default)
python3 post-install.py

# Install specific categories
python3 post-install.py --categories essential development python

# Install everything except multimedia
python3 post-install.py --categories essential development python research productivity
```

### Interactive Mode
```bash
# Let users choose what to install
python3 post-install.py --interactive --categories essential development
```

### Testing and Debugging
```bash
# Preview what would be installed
python3 post-install.py --dry-run --verbose

# Check what categories are available
python3 post-install.py --help
```

### Safety and Rollback
```bash
# Exclude specific software
python3 post-install.py --exclude docker nodejs

# Rollback last installation session
python3 post-install.py --rollback

# Skip system upgrades
python3 post-install.py --no-upgrade
```

### Custom Logging
```bash
# Custom log location
python3 post-install.py --log-file /tmp/install.log --state-file /tmp/state.json
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-v, --verbose` | Enable verbose logging |
| `-d, --dry-run` | Preview commands without executing |
| `-i, --interactive` | Interactive software selection |
| `--rollback` | Rollback previous installation |
| `--no-upgrade` | Skip apt upgrade step |
| `--categories` | Specify categories to install |
| `--exclude` | Exclude specific software |
| `--log-file` | Custom log file path |
| `--state-file` | Custom state file path |

## File Structure

```
post-install.py          # Main script
post-install.log         # Execution log (created automatically)
post-install-state.json  # Installation state tracking (created automatically)
README.md               # This documentation
```

## State Management

The script maintains a JSON state file (`post-install-state.json`) that tracks:
- Installation attempts with timestamps
- Success/failure status
- Package lists for each software
- Installation methods used
- Software categories

This enables:
- **Idempotent operations**: Skip already installed software
- **Rollback functionality**: Undo recent installations
- **Installation history**: Track what was installed when
- **Resume capability**: Continue after interruptions

## Extending the Script

### Adding New Software

1. **Choose appropriate category** or create a new one in `SoftwareCategory`
2. **Add to SOFTWARE_CATALOG** with this structure:
```python
"software-name": {
    "packages": ["package1", "package2"],  # Empty for custom installs
    "method": "apt|snap|custom",           # Installation method
    "description": "Brief description"      # User-friendly description
}
```

3. **For custom installations**: Add function to `install_custom_software()`

### Adding Research Group Specific Software

To customize for your research group, consider:

1. **Create new categories** (e.g., `BIOINFORMATICS`, `MACHINE_LEARNING`)
2. **Add domain-specific tools**:
   - Computational biology tools
   - Statistical software
   - Specialized libraries
   - Group-specific configurations

3. **Custom installation methods** for:
   - Conda environments
   - Docker containers
   - Custom compiled software
   - License-managed software

## Best Practices

### For System Administrators
- **Test with `--dry-run`** before actual deployment
- **Use state files** to track lab-wide installations
- **Customize categories** for your research domain
- **Set up logging** in a centralized location

### For Users
- **Start with essential** category for basic setup
- **Use interactive mode** when unsure about software needs
- **Keep state files** for rollback capability
- **Review logs** if installations fail

### For Developers
- **Add error handling** for new installation methods
- **Test rollback functionality** for new software
- **Update documentation** when adding features
- **Maintain category organization** for clarity

## Troubleshooting

### Common Issues

1. **Permission errors**: Run with `sudo` for system packages
2. **Network issues**: Check internet connectivity for downloads
3. **Package conflicts**: Use `--exclude` to skip problematic packages
4. **Partial installations**: Use `--rollback` to clean up

### Recovery Steps

1. **Check logs** in `post-install.log` for detailed error information
2. **Use rollback** if installation partially succeeded
3. **Verify system state** with `--dry-run` mode
4. **Exclude problematic packages** and retry

### Getting Help

1. **Run with `--help`** for usage information
2. **Check verbose logs** with `-v` flag
3. **Test with dry run** to understand behavior
4. **Review state file** for installation history

## Security Considerations

- **Script verification**: Review script contents before execution
- **Network downloads**: Custom installers download from official sources
- **Package verification**: Uses system package managers with verification
- **State file protection**: Contains installation history (not sensitive)
- **Log file security**: May contain system information

## Contributing

When extending this script:

1. **Maintain backwards compatibility**
2. **Add comprehensive error handling**
3. **Update documentation**
4. **Test rollback functionality**
5. **Follow existing code patterns**
6. **Consider cross-platform compatibility**

## License

This script is designed for research group use. Modify and distribute according to your institution's policies.
