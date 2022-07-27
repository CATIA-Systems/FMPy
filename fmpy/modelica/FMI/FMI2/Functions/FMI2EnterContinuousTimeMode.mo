within FMI.FMI2.Functions;
impure function FMI2EnterContinuousTimeMode
  input Internal.ExternalFMU externalFMU;
    external"C" FMU_FMI2EnterContinuousTimeMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2EnterContinuousTimeMode;
