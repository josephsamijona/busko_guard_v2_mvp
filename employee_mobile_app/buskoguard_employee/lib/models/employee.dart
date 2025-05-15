class User {
  final int id;
  final String username;
  final String firstName;
  final String lastName;
  final String email;
  final String? dateOfBirth;
  final String? phoneNumber;
  final String? address;
  final String? profilePicture;

  User({
    required this.id,
    required this.username,
    required this.firstName,
    required this.lastName,
    required this.email,
    this.dateOfBirth,
    this.phoneNumber,
    this.address,
    this.profilePicture,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      email: json['email'] ?? '',
      dateOfBirth: json['date_of_birth'],
      phoneNumber: json['phone_number'],
      address: json['address'],
      profilePicture: json['profile_picture'],
    );
  }
}

class Department {
  final int id;
  final String name;
  final String? description;

  Department({
    required this.id,
    required this.name,
    this.description,
  });

  factory Department.fromJson(Map<String, dynamic> json) {
    return Department(
      id: json['id'],
      name: json['name'],
      description: json['description'],
    );
  }
}

class Role {
  final int id;
  final String name;
  final String? description;

  Role({
    required this.id,
    required this.name,
    this.description,
  });

  factory Role.fromJson(Map<String, dynamic> json) {
    return Role(
      id: json['id'],
      name: json['name'],
      description: json['description'],
    );
  }
}

class Employee {
  final String employeeId;
  final User user;
  final Department? department;
  final Role? role;
  final String? nfcId;
  final String? qrCode;
  final String? qrCodeImage;
  final String fullName;

  Employee({
    required this.employeeId,
    required this.user,
    this.department,
    this.role,
    this.nfcId,
    this.qrCode,
    this.qrCodeImage,
    required this.fullName,
  });

  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      employeeId: json['employee_id'],
      user: User.fromJson(json['user']),
      department: json['department'] != null 
          ? Department.fromJson(json['department']) 
          : null,
      role: json['role'] != null 
          ? Role.fromJson(json['role']) 
          : null,
      nfcId: json['nfc_id'],
      qrCode: json['qr_code'],
      qrCodeImage: json['qr_code_image'],
      fullName: json['full_name'] ?? '${json['user']['first_name']} ${json['user']['last_name']}',
    );
  }
}